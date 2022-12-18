# -*- coding: utf-8 -*-
import datetime
import json
import logging
from copy import deepcopy

from django.core.paginator import InvalidPage, Paginator
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q, F
from django.db.models.constants import LOOKUP_SEP
from django.db.models.expressions import OrderBy
from django.http import Http404
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.translation import gettext_lazy as _

from . import constants


logger = logging.getLogger(__name__)


def paginate_queryset(queryset, page, page_size):
	"""
	Shortcut to paginate queryset
	"""
	paginator = Paginator(queryset, page_size)
	try:
		page_number = int(page)
	except ValueError:
		raise Http404(_("Page is not number."))

	try:
		page = paginator.page(page_number)
		return (paginator, page, page.object_list, page.has_other_pages())
	except InvalidPage as e:
		raise Http404(_('Invalid page (%(page_number)s): %(message)s') % {'page_number': page_number, 'message': str(e)})


def get_model_attribute(obj, attribute):
	"""
	Get model attribute by traversing attributes by django path like review__book
	"""
	for lookup in attribute.split(LOOKUP_SEP):
		obj = getattr(obj, lookup)
	return obj


def get_order_key(obj, order_by):
	"""
	Get list of attributes for order key, e.g. if order_key is ['pk'], it will
	return [obj.pk]
	"""
	return tuple(
		get_model_attribute(obj, f.expression.name if isinstance(f, OrderBy) else f.lstrip('-'))
		for f in order_by
	)


def url_decode_order_key(order_key):
	"""
	Encode list of order keys to URL string
	"""
	return tuple(json.loads(urlsafe_base64_decode(order_key).decode('utf-8')))


def url_encode_order_key(value):
	"""
	Decode list of order keys from URL string
	"""
	# prevent microsecond clipping
	value = [v.isoformat() if isinstance(v, datetime.datetime) else v for v in value]
	return urlsafe_base64_encode(json.dumps(value, cls=DjangoJSONEncoder).encode('utf-8'))


def get_order_by(qs):
	"""
	Returns order_by from queryset
	"""
	query = qs.query
	return query.order_by or query.get_meta().ordering


def invert_order_by(order_by):
	"""
	Invert list of OrderBy expressions
	"""
	order_by = deepcopy(order_by)
	for field in order_by:
		# invert asc / desc
		field.descending = not field.descending

		# invert nulls first / last (only one can be active)
		if field.nulls_first:
			field.nulls_first = None
			field.nulls_last = True
		elif field.nulls_last:
			field.nulls_last = None
			field.nulls_first = True

	return order_by


def convert_to_order_by(field):
	"""
	Converts field name to OrderBy expression
	"""
	if isinstance(field, OrderBy):
		return field
	return F(field[1:]).desc() if field[:1] == '-' else F(field).asc()


def convert_order_by_to_expressions(order_by):
	"""
	Converts list of order_by keys like ['pk'] to list of OrderBy objects
	"""
	return [convert_to_order_by(field) for field in order_by]


def filter_by_order_key(qs, direction, start_position):
	"""
	Filter queryset from specific position inncluding start position
	"""

	# change list of strings or expressions to list of expressions
	order_by = convert_order_by_to_expressions(get_order_by(qs))

	# check if we have required start_position
	if len(start_position) != len(order_by):
		raise InvalidPage()

	# invert order
	if direction == constants.KEY_BACK:
		order_by = invert_order_by(order_by)
		qs = qs.order_by(*order_by)

	filter_combinations = {}
	q = Q() # final filter

	# create chain of rule rule for example for name="x" parent=1, id=2 will be following:
	# name > 'x' OR name = 'x' AND parent > 1 OR name = 'x' AND parent = 1 AND id >= 2
	for i, value in enumerate(zip(order_by, start_position)):
		# unpack values
		order_expression, value = value

		# last tieration
		is_last = i == len(order_by) - 1

		# filter by
		field_name = order_expression.expression.name

		field_lookup = ''

		# Value  Order (NULL)  First condition    Next condition
		# ------------------------------------------------------
		# Val    Last          >< Val | NULL      =Val
		# Val    First         >< Val             =Val
		# NULL   Last          SKIP               =NULL
		# NULL   First         NOT NULL           =NULL

		if value is None: # special NULL handling
			if order_expression.nulls_last:
				field_lookup = f'{field_name}__isnull'
				filter_combinations[field_lookup] = True
				continue
			if order_expression.nulls_first:
				filter_combinations[f'{field_name}__isnull'] = False
				q |= Q(**filter_combinations)
				filter_combinations[f'{field_name}__isnull'] = True
				continue
			else:
				logger.warning("No nulls_first / nulls_last specified")
		else:
			# smaller or greater
			direction = 'lt' if order_expression.descending else 'gt'
			if is_last: # change > to >= and < to <= on last iteration
				direction = f'{direction}e'

			# construct field lookup
			field_lookup = f'{field_name}__{direction}'

			# set lookup to current combination
			if order_expression.nulls_last:
				filter_combination = (
					Q(**filter_combinations) &
					(Q(**{field_lookup: value}) | Q(**{f'{field_name}__isnull': True}))
				)
				q |= filter_combination
				filter_combinations[field_name] = value
				continue
			else:
				filter_combinations[field_lookup] = value

		# apply combination
		filter_combination = Q(**filter_combinations)
		q |= filter_combination

		# transform >, < to equals
		filter_combinations.pop(field_lookup, None)
		filter_combinations[field_name] = value

	# apply filter
	if q:
		try:
			qs = qs.filter(q)
		except Exception:
			raise InvalidPage()

	return qs
