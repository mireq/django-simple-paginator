# -*- coding: utf-8 -*-
from django.db.models import F
from django.http import Http404
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import datetime

from .models import Book, Review
from django_simple_paginator.converter import PageConverter
from django_simple_paginator.utils import paginate_queryset, get_model_attribute, get_order_key, url_encode_order_key, url_decode_order_key, invert_order_by


class TestPageConverter(TestCase):
	def test_to_pyton(self):
		converter = PageConverter()
		self.assertEqual(1, converter.to_python('')) # empty
		self.assertEqual(2, converter.to_python('2'))
		self.assertEqual(2, converter.to_python('2/'))

	def test_to_url(self):
		converter = PageConverter()
		self.assertEqual('', converter.to_url('')) # empty
		self.assertEqual('', converter.to_url(1)) # first page ommited
		self.assertEqual('', converter.to_url('1')) # compatible with strings
		self.assertEqual('2/', converter.to_url('2'))

	def test_urlconf(self):
		self.assertEqual('/page/', reverse('page', kwargs={'page': 1}))
		self.assertEqual('/page/', reverse('page', kwargs={'page': '1'}))
		self.assertEqual('/page/2/', reverse('page', kwargs={'page': 2}))
		self.assertEqual('/page/2/', reverse('page', kwargs={'page': '2'}))


class TestUtils(TestCase):
	def test_paginate_queryset(self):
		books = [Book(name="1"), Book(name="2"), Book(name="3")]
		Book.objects.bulk_create(books)
		qs = Book.objects.order_by('pk')
		books = list(qs)

		with self.assertRaises(Http404):
			paginate_queryset(qs, page="invalid", page_size=2)

		with self.assertRaises(Http404):
			paginate_queryset(qs, page=20, page_size=2)

		paginator, page, object_list, has_others = paginate_queryset(qs, page=2, page_size=2)

		self.assertEqual(2, paginator.per_page)
		self.assertTrue(page.has_previous())
		self.assertFalse(page.has_next())
		self.assertEqual(3, page.end_index())
		self.assertEqual(books[2:], list(object_list))
		self.assertTrue(has_others)

	def test_get_model_attribute(self):
		book = Book.objects.create(name="book")
		review = Review.objects.create(book=book, text="review")

		self.assertEqual("review", get_model_attribute(review, "text"))
		self.assertEqual("book", get_model_attribute(review, "book__name"))

	def test_get_order_key(self):
		book = Book.objects.create(name="book")
		review = Review.objects.create(book=book, text="review")

		# simple case
		self.assertEqual(
			(book.pk,),
			get_order_key(book, ['pk'])
		)

		# negative are supported too
		self.assertEqual(
			(book.pk,),
			get_order_key(book, ['-pk'])
		)

		# f expression
		self.assertEqual(
			(book.pk,),
			get_order_key(book, [F('pk').desc()])
		)

		# multiple values
		self.assertEqual(
			(review.pk, review.book_id, review.book.name),
			get_order_key(review, ['pk', 'book_id', 'book__name'])
		)

	def test_encode_order_key(self):
		# empty
		order_key = ()
		self.assertEqual(order_key, url_decode_order_key(url_encode_order_key(order_key)))

		# single value
		order_key = (1,)
		self.assertEqual(order_key, url_decode_order_key(url_encode_order_key(order_key)))

		# None
		order_key = (None,)
		self.assertEqual(order_key, url_decode_order_key(url_encode_order_key(order_key)))

		# different values
		order_key = (1, "text")
		self.assertEqual(order_key, url_decode_order_key(url_encode_order_key(order_key)))

		# datetime
		order_key = (timezone.now(),)
		processed_order_key = url_decode_order_key(url_encode_order_key(order_key))
		processed_order_key = (datetime.fromisoformat(processed_order_key[0]),)
		self.assertEqual(order_key, processed_order_key)

	def test_invert_order_by(self):
		order_by = [F('name').asc()]
		inverted = [F('name').desc()]
		self.assertOrderByEqual(inverted[0], invert_order_by(order_by)[0])
		order_by = [F('name').desc()]
		inverted = [F('name').asc()]
		self.assertOrderByEqual(inverted[0], invert_order_by(order_by)[0])
		order_by = [F('name').asc(nulls_first=True)]
		inverted = [F('name').desc(nulls_last=True)]
		self.assertOrderByEqual(inverted[0], invert_order_by(order_by)[0])
		order_by = [F('name').asc(nulls_last=True)]
		inverted = [F('name').desc(nulls_first=True)]
		self.assertOrderByEqual(inverted[0], invert_order_by(order_by)[0])

	def assertOrderByEqual(self, a, b):
		self.assertTrue(a.descending == b.descending and bool(a.nulls_first) == bool(b.nulls_first) and bool(a.nulls_last) == bool(b.nulls_last))
