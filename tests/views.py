# -*- coding: utf-8 -*-
from django.views.generic import ListView

from .models import Book


class BookList(ListView):
	template_name = 'example.html'
	paginate_by = 2
	queryset = Book.objects.order_by('pk')
