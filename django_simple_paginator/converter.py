# -*- coding: utf-8 -*-
class PageConverter:
	"""
	Converts from / to paginated URL
	"""
	regex = r'(?:\d+/)?'

	def to_python(self, value):
		value = value.rstrip('/')
		if value:
			return int(value)
		else:
			return 1

	def to_url(self, value):
		if not value:
			return ''
		value = int(value)
		if value == 1:
			return ''
		else:
			return '%d/' % value


class CursorPageConverter:
	"""
	Converts cursor page from / to paginated URL
	"""
	regex = r'(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?'

	def to_python(self, value):
		value = value.rstrip('/')
		return value or 1

	def to_url(self, value):
		if not value or value == 1:
			return ''
		else:
			return '%s/' % value
