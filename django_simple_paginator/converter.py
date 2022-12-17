# -*- coding: utf-8 -*-
class PageConverter:
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
