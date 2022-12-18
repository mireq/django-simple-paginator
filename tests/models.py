# -*- coding: utf-8 -*-
from django.db import models
from django.utils import timezone


class Book(models.Model):
	name = models.CharField(max_length=50)
	is_published = models.BooleanField(default=True)
	pub_time = models.DateTimeField(default=timezone.now)
	rating = models.FloatField(blank=True, null=True)

	def __str__(self):
		return f'#{self.pk} {self.name}, published: {self.is_published} ({self.pub_time.isoformat()}), rating: {self.rating}'


class BookOrdered(Book):
	class Meta:
		ordering = ('pk',)
		proxy = True


class Review(models.Model):
	book = models.ForeignKey(Book, on_delete=models.CASCADE)
	text = models.CharField(max_length=50)

	def __str__(self):
		return f'#{self.pk} {self.book_id} {self.text}'

	class Meta:
		ordering = ('pk',)
