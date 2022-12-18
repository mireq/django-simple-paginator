# -*- coding: utf-8 -*-
from django.urls import path, register_converter

from django_simple_paginator.converter import PageConverter
from .views import BookList


register_converter(PageConverter, 'page')


urlpatterns = [
	path('page/<page:page>', BookList.as_view(), name='page'),
	path('using-get/', BookList.as_view(), name='using_get'),
]
