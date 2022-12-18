# -*- coding: utf-8 -*-
from django.urls import path, register_converter

from .views import BookList, CursorBookList
from django_simple_paginator.converter import PageConverter, CursorPageConverter


register_converter(PageConverter, 'page')
register_converter(CursorPageConverter, 'cursor_page')


urlpatterns = [
	path('page/<page:page>', BookList.as_view(), name='page'),
	path('using-get/', BookList.as_view(), name='using_get'),
	path('cursor/<cursor_page:page>', CursorBookList.as_view(), name='cursor_page'),
]
