# -*- coding: utf-8 -*-
from django.test import TestCase
from .models import Book


class TestFirstPage(TestCase):
	def test_model(self):
		Book.objects.create(name="a", pages=10, is_published=True)
		print(Book.objects.all())
