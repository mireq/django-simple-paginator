# -*- coding: utf-8 -*-
from django.core.paginator import Paginator, Page
from django.utils.functional import cached_property
from django.db.models.expressions import OrderBy
from django.db.models import F
from django.core.paginator import InvalidPage
from django.utils.translation import gettext
import collections.abc
from functools import partial
from . import utils


class CursorPage(Page):
	next_page_item = None
	prev_page_item = None
	first_item = None
	last_item = None
	initialized = False

	def has_next(self):
		self.initialize()
		return self.next_page_item is not None

	def has_previous(self):
		self.initialize()
		return self.prev_page_item is not None

	def next_page_number(self):
		self.initialize()
		page_desc = self.encode_order_key(self.paginator.get_order_key(self.last_item))
		return 'f' + page_desc

	def previous_page_number(self):
		self.initialize()
		page_desc = self.encode_order_key(self.paginator.get_order_key(self.first_item))
		return 'b' + page_desc

	def initialize(self):
		if self.initialized:
			return
		self.initialized = True
		next(iter(self.object_list))

	def encode_order_key(self, value):
		return utils.encode_order_key(value)


class IteratorWrapper(object):
	def __init__(self, iterator_class, paginator, page, *args, **kwargs):
		self.iterator = iterator_class(*args, **kwargs)
		self.paginator = paginator
		self.page = page
		self._result_cache = None

	def __iter__(self):
		if self._result_cache is None:
			self._result_cache = list(self.iterator)
			start_key = self.paginator.get_start_order_key(self.page.number)

			if start_key is not None:
				# first hidden item used to render previous link
				if self._result_cache and self.paginator.get_order_key(self._result_cache[0]) == start_key:
					self.page.prev_page_item = self._result_cache.pop(0)

			# hide lastitem
			if len(self._result_cache) > self.paginator.per_page:
				self.page.next_page_item = self._result_cache.pop()

			if self._result_cache:
				self.page.first_item = self._result_cache[0]
				self.page.last_item = self._result_cache[-1]

		return iter(self._result_cache)


class CursorPaginator(Paginator):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		order_by = []
		for field in self.object_list.query.order_by:
			if isinstance(field, OrderBy):
				order_by.append(field)
			else:
				reverse = field[:1] == '-'
				field = field.lstrip('-')
				if reverse:
					order_by.append(F(field).desc())
				else:
					order_by.append(F(field).asc())

		self.order_by = order_by
		self.per_page = 1

	def validate_number(self, number):
		if not number or not isinstance(number, str):
			return None
		direction = number[:1]
		if direction not in {'f', 'b'}:
			raise self.raise_invalid_page_format()
		number = [direction] + utils.decode_order_key(number[1:])
		print(number)
		#try:
		#	number = [direction] + utils.decode_order_key(number[1:])
		#except Exception:
		#	self.raise_invalid_page_format()
		return number

	def raise_invalid_page_format(self):
		raise InvalidPage(gettext("Invalid page format"))

	def page(self, number):
		print(number)
		page = CursorPage(None, number, self)
		limited = self.object_list[1:4]
		limited._iterable_class = partial(IteratorWrapper, limited._iterable_class, self, page)
		page.object_list = limited
		return page

	@cached_property
	def count(self):
		return 0

	@cached_property
	def num_pages(self):
		return 0

	def get_start_order_key(self, number):
		print(number)
		return number
		#return (number+51741,)

	def get_order_by_keys(self):
		return [k.lstrip('-') for k in self.order_by]

	def get_order_key(self, obj):
		return utils.get_order_key(obj, self.order_by)
