# -*- coding: utf-8 -*-
from django.core.paginator import Paginator as OrigPaginator, Page as OrigPage

from .settings import PAGINATOR_INNER_COUNT, PAGINATOR_OUTER_COUNT


class Page(OrigPage):
	def __init__(self, *args, **kwargs):
		super(Page, self).__init__(*args, **kwargs)
		self.page_range = []
		self.next = None
		self.previous = None

		ranges = []
		ranges.append((1, min(self.paginator.num_pages, self.paginator.outer)))
		ranges.append((max(self.number - self.paginator.inner, 1), min(self.number + self.paginator.inner, self.paginator.num_pages)))
		ranges.append((max(self.paginator.num_pages + 1 - self.paginator.outer, 1), (self.paginator.num_pages)))

		newRanges = []
		currentRange = (1, 1)
		for r in ranges:
			# Spojenie
			if currentRange[1] >= r[0] - 1:
				currentRange = (currentRange[0], r[1])
			else:
				newRanges.append(currentRange)
				currentRange = r

		if not currentRange is None:
			newRanges.append(currentRange)

		for r in newRanges:
			self.page_range += range(r[0], r[1] + 1)
			self.page_range.append(None)

		if self.page_range and self.page_range[-1] is None:
			self.page_range = self.page_range[0:-1]


class Paginator(OrigPaginator):
	def __init__(self, *args, **kwargs):
		self.inner = kwargs.pop("inner", PAGINATOR_INNER_COUNT)
		self.outer = kwargs.pop("outer", PAGINATOR_OUTER_COUNT)
		super(Paginator, self).__init__(*args, **kwargs)

	def _get_page(self, *args, **kwargs):
		return Page(*args ,**kwargs)
