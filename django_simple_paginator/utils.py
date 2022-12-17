# -*- coding: utf-8 -*-
import datetime
import struct
from io import BytesIO, BufferedReader

from django.core.paginator import InvalidPage, Paginator
from django.http import Http404
from django.utils.duration import duration_iso_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.translation import gettext_lazy as _


def paginate_queryset(queryset, page, page_size):
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


def get_model_field_by_path(obj, path):
	for lookup in path.split('__'):
		obj = getattr(obj, lookup)
	return obj


def get_order_key(obj, order_by):
	return tuple(get_model_field_by_path(obj, expr.expression.name) for expr in order_by)


def value_to_str(val):
	if isinstance(val, (datetime.datetime, datetime.date, datetime.time)):
		return val.isoformat()
	elif isinstance(val, datetime.timedelta):
		return duration_iso_string(val)
	else:
		return str(val)


def decode_order_key(order_key):
	order_key = urlsafe_base64_decode(order_key)
	data = BytesIO(order_key)
	data.seek(0)
	stream = BufferedReader(data)

	parts = []

	while True:
		size = stream.peek(1)[:1]
		if not size:
			break
		size = struct.unpack('B', size)[0]
		if size < 128:
			stream.read(1)
		else:
			size = stream.read(4)
			if len(size) != 4:
				raise ValueError("Truncated order key")
			size = (struct.unpack('>L', size)[0] & 0x7fffffff) + 128;
		parts.append(stream.read(size).decode('utf-8'))

	return parts


def encode_order_key(value):
	value = [value_to_str(component) for component in value]
	# construct packed list of strings
	data = BytesIO()
	for component in value:
		component = component.encode('utf-8')
		if len(component) < 128:
			data.write(struct.pack('B', len(component)))
		else:
			# big endian starting with 1 on most significant place
			data.write(struct.pack('>L', (len(component) - 128) | 0x80000000))
		data.write(component)
	return urlsafe_base64_encode(data.getvalue())
