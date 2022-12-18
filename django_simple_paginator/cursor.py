# -*- coding: utf-8 -*-
from collections import namedtuple
from functools import partial

from django.core.paginator import InvalidPage, Paginator, Page
from django.http import Http404
from django.utils.functional import cached_property
from django.utils.translation import gettext, gettext_lazy as _

from . import constants, utils


OrderKeyFilter = namedtuple('OrderKeyFilter', ['direction', 'values'])


class CursorPage(Page):
	next_page_item = None
	prev_page_item = None
	first_item = None
	last_item = None

	def has_next(self):
		return self.next_page_item is not None

	def has_previous(self):
		return self.prev_page_item is not None

	def next_page_number(self):
		page_desc = self.url_encode_order_key(self.paginator.get_order_key(self.last_item))
		return constants.KEY_NEXT + page_desc

	def previous_page_number(self):
		page_desc = self.url_encode_order_key(self.paginator.get_order_key(self.first_item))
		return constants.KEY_BACK + page_desc

	def url_encode_order_key(self, value):
		return utils.url_encode_order_key(value)


class IteratorWrapper(object):
	def __init__(self, iterator_class, paginator, page, *args, **kwargs):
		self.iterator = iterator_class(*args, **kwargs)
		self.paginator = paginator
		self.page = page

	@cached_property
	def _result_cache(self):
		cache = list(self.iterator)
		start_key = self.paginator.get_start_order_key(self.page.number)

		if start_key is not None:
			# first item handling (used to check previous page existence)
			if cache and self.paginator.get_order_key(cache[0]) == start_key.values:
				if start_key.direction == constants.KEY_BACK:
					self.page.next_page_item = cache.pop(0)
				else:
					self.page.prev_page_item = cache.pop(0)

		# last item handling (used to check previous page existence)
		if len(cache) > self.paginator.per_page:
			if start_key is not None and start_key.direction == constants.KEY_BACK:
				self.page.prev_page_item = cache.pop()
			else:
				self.page.next_page_item = cache.pop()

		# revert backwards iterated queryset
		if start_key is not None and start_key.direction == constants.KEY_BACK:
			cache = cache[::-1]

		# set first and last items of page
		if cache:
			self.page.first_item = cache[0]
			self.page.last_item = cache[-1]

		return cache

	def __iter__(self):
		return iter(self._result_cache)


class CursorPaginator(Paginator):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.order_by = utils.convert_order_by_to_expressions(utils.get_order_by(self.object_list))

	def validate_number(self, number):
		if not number or not isinstance(number, str):
			return None
		direction = number[:1]
		if direction not in {constants.KEY_BACK, constants.KEY_NEXT}:
			raise self.raise_invalid_page_format()
		try:
			return OrderKeyFilter(direction, utils.url_decode_order_key(number[1:]))
		except Exception:
			self.raise_invalid_page_format()

	def raise_invalid_page_format(self):
		raise InvalidPage(gettext("Invalid page format"))

	def page(self, number):
		order_key_filter = self.validate_number(number)
		page = CursorPage(None, order_key_filter, self)
		count = self.per_page + (2 if order_key_filter else 1) # load one more item before and after list
		qs = self.object_list
		if order_key_filter:
			qs = utils.filter_by_order_key(qs, order_key_filter.direction, order_key_filter.values)
		qs = qs[:count]
		qs._iterable_class = partial(IteratorWrapper, qs._iterable_class, self, page)
		page.object_list = qs
		# force initialization
		try:
			next(iter(qs))
		except StopIteration:
			pass
		return page

	@cached_property
	def count(self):
		return 0

	@cached_property
	def num_pages(self):
		return 0

	def get_start_order_key(self, number):
		return number

	def get_order_key(self, obj):
		return utils.get_order_key(obj, self.order_by)


def paginate_cursor_queryset(queryset, page_number, page_size):
	"""
	Shortcut to paginate cursor queryset
	"""
	try:
		paginator = CursorPaginator(queryset, page_size)
		page = paginator.page(page_number)
		return (paginator, page, page.object_list, page.has_other_pages())
	except InvalidPage:
		raise Http404(_('Invalid page link'))


class CursorPaginateMixin(object):
	"""
	Used to replace paginate_by method of ListView
	"""
	paginator_class = CursorPaginator

	def paginate_queryset(self, queryset, page_size):
		page_kwarg = self.page_kwarg
		page_number = self.kwargs.get(page_kwarg) or self.request.GET.get(page_kwarg) or 1
		return paginate_cursor_queryset(queryset, page_number, page_size)
