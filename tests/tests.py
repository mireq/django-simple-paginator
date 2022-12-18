# -*- coding: utf-8 -*-
from django.db.models import F
from django.http import Http404
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import datetime
from pprint import pprint
from django.core.paginator import InvalidPage

from .models import Book, Review
from django_simple_paginator import constants
from django_simple_paginator.converter import PageConverter
from django_simple_paginator.utils import paginate_queryset, get_model_attribute, get_order_key, url_encode_order_key, url_decode_order_key, invert_order_by, convert_to_order_by, convert_order_by_to_expressions, filter_by_order_key


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

	def test_convert_order_by_to_expressions(self):
		e = convert_to_order_by('pk')
		self.assertEqual(e.expression.name, 'pk')
		self.assertFalse(e.descending)

		e = convert_to_order_by('-pk')
		self.assertEqual(e.expression.name, 'pk')
		self.assertTrue(e.descending)

		# conversion not needed
		e = convert_to_order_by(F('pk').asc())
		self.assertEqual(e.expression.name, 'pk')

		e = convert_order_by_to_expressions(['pk'])
		self.assertEqual(e[0].expression.name, 'pk')
		self.assertFalse(e[0].descending)

	def assertOrderByEqual(self, a, b):
		self.assertTrue(a.descending == b.descending and bool(a.nulls_first) == bool(b.nulls_first) and bool(a.nulls_last) == bool(b.nulls_last))

	def test_filter_by_order_key(self):
		book_list = [
			Book(id=1, pub_time='1970-01-01T00:00:00', name="A"),
			Book(id=2, pub_time='1970-01-02T00:00:00', name="A", rating=2.0),
			Book(id=3, pub_time='1970-01-03T00:00:00', name="A", rating=3.0),
			Book(id=4, pub_time='1970-01-04T00:00:00', name="B"),
			Book(id=5, pub_time='1970-01-05T00:00:00', name="B"),
		]
		Book.objects.bulk_create(book_list)
		book_list = list(Book.objects.order_by('pk'))

		def get_books(order, values=(), backwards=False):
			direction = constants.KEY_BACK if backwards else constants.KEY_NEXT
			books = Book.objects.order_by(*order).values_list('pk', flat=True)
			return list(filter_by_order_key(books, direction, values, books.query.order_by))

		with self.assertRaises(InvalidPage):
			books = get_books([F("pk").asc()], []) # missing parameter

		with self.assertRaises(InvalidPage):
			books = get_books([F("pk").asc()], ['x']) # wrong value

		# empty filter
		books = get_books([], [])
		self.assertEqual([1, 2, 3, 4, 5], books)

		# from 3 forwards
		books = get_books([F("pk").asc()], [3])
		self.assertEqual([3, 4, 5], books)

		# from 3 backwards
		books = get_books([F("pk").asc()], [3], backwards=True) # from 3 backwards
		self.assertEqual([3, 2, 1], books)

		# reverse
		books = get_books([F("pk").desc()], [3])
		self.assertEqual([3, 2, 1], books)
		books = get_books([F("pk").desc()], [3], backwards=True)
		self.assertEqual([3, 4, 5], books)
