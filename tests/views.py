# -*- coding: utf-8 -*-
from django.views.generic import ListView
from django_simple_paginator.cursor import CursorPaginateMixin

from .models import Book


class BookList(ListView):
	template_name = 'example.html'
	paginate_by = 2
	queryset = Book.objects.order_by('pk')

	def get_template_names(self):
		if self.request.GET.get('engine') == 'jinja':
			return ['example.jinja']
		else:
			return [self.template_name]

	def get_context_data(self, **kwargs):
		return super().get_context_data(extra={}, **kwargs)


class CursorBookList(CursorPaginateMixin, BookList):
	pass
