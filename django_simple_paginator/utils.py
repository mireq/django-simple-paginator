# -*- coding: utf-8 -*-
import datetime
import json
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


def filter_by_order_key(qs, direction, start_position, order_by):
	"""
	Filter queryset from specific position inncluding start position
	"""

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
		order_key, value = value
		# smaller or greater
		direction = 'lt' if order_key.descending else 'gt'
		if i == len(order_by) - 1: # change > to >= and < to <= on last iteration
			direction = f'{direction}e'

		# construct field lookup
		field_name = order_key.expression.name
		field_lookup = f'{field_name}__{direction}'

		# set lookup to current combination
		filter_combinations[field_lookup] = value

		# apply combination
		q |= Q(**filter_combinations)

		# transform >, < to equals
		del filter_combinations[field_lookup]
		filter_combinations[field_name] = value

	# apply filter
	if q:
		try:
			qs = qs.filter(q)
		except Exception:
			raise InvalidPage()

	return qs
