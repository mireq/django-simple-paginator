# -*- coding: utf-8 -*-
from django.urls import path, register_converter

from django_simple_paginator.converter import PageConverter


def view(request):
	pass



register_converter(PageConverter, 'page')


urlpatterns = [
	path('page/<page:page>', view, name='page'),
]
