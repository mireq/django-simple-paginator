# -*- coding: utf-8 -*-
import datetime
import json
from copy import deepcopy

from django.core.paginator import InvalidPage, Paginator
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q
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
		# invert ASC/DESC
		field.descending = not field.descending

		# invert nulls first / last (only one can be active)
		if field.nulls_first:
			field.nulls_first = None
			field.nulls_last = True
		elif field.nulls_last:
			field.nulls_last = None
			field.nulls_first = True

	return order_by


def filter_by_order_key(qs, direction, values, order_by):
	if direction == constants.KEY_BACK:
		order_by = invert_order_by(order_by)
		qs = qs.order_by(*order_by)

	filter_chain = {}
	q = Q()

	for order_key, value in zip(order_by, values):
		direction = '__lt' if order_key.descending else '__gt'
		filter_chain[order_key.expression.name + direction] = value
		q |= Q(**filter_chain)
		del filter_chain[order_key.expression.name + direction]
		filter_chain[order_key.expression.name] = value

	if filter_chain:
		q |= Q(**filter_chain)

	if q:
		qs = qs.filter(q)

	return qs
