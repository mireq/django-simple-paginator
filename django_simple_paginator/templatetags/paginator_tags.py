# -*- coding: utf-8 -*-
from django import template
from django.urls import reverse, NoReverseMatch
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string

from ..settings import PAGINATOR_INNER_COUNT, PAGINATOR_OUTER_COUNT


register = template.Library()


def assign_range_to_page_obj(page_obj, inner, outer):
	page_obj.page_range = []

	ranges = []
	ranges.append((1, min(page_obj.paginator.num_pages, outer)))
	ranges.append((max(page_obj.number - inner, 1), min(page_obj.number + inner, page_obj.paginator.num_pages)))
	ranges.append((max(page_obj.paginator.num_pages + 1 - outer, 1), (page_obj.paginator.num_pages)))

	new_ranges = []
	current_range = (1, 1)
	for r in ranges:
		# Spojenie
		if current_range[1] >= r[0] - 1:
			current_range = (current_range[0], r[1])
		else:
			new_ranges.append(current_range)
			current_range = r

	if not current_range is None:
		new_ranges.append(current_range)

	for r in new_ranges:
		page_obj.page_range += range(r[0], r[1] + 1)
		page_obj.page_range.append(None)

	if page_obj.page_range and page_obj.page_range[-1] is None:
		page_obj.page_range = page_obj.page_range[0:-1]
	return page_obj


def pagination_ctx(context, page_obj, page_kwarg, inner, outer, url_name, url_args, url_kwargs):
	page_obj = page_obj or context['page_obj']
	if hasattr(context, 'flatten'):
		inner_context = context.flatten()
	else:
		inner_context = dict(context)
	if url_name is None:
		request = context['request']
		resolver_match = request.resolver_match
		url_name = resolver_match.view_name
		url_args = resolver_match.args
		url_kwargs = resolver_match.kwargs
	else:
		url_args = url_args or []
		url_kwargs = url_kwargs or {}
	ctx_update = {
		'page_obj': assign_range_to_page_obj(page_obj, inner, outer),
		'page_kwarg': page_kwarg,
		'url_name': url_name,
		'url_args': url_args,
		'url_kwargs': url_kwargs,
	}
	inner_context.update(ctx_update)
	return inner_context


@register.simple_tag(takes_context=True)
def pagination(context, page_obj=None, page_kwarg='page', template_name='paginator/paginator.html', inner=PAGINATOR_INNER_COUNT, outer=PAGINATOR_OUTER_COUNT, url_name=None, *url_args, **url_kwargs): # pylint: disable=too-many-arguments
	rendered = render_to_string(template_name, pagination_ctx(context, page_obj, page_kwarg, inner, outer, url_name, url_args, url_kwargs))
	return mark_safe(rendered)


@register.simple_tag(takes_context=True)
def pager_url(context, page_num):
	request = context['request']
	url_name = context['url_name']
	url_args = context['url_args']
	url_kwargs = context['url_kwargs']
	page_kwarg = context['page_kwarg']
	kwargs = {k: v for k, v in url_kwargs.items() if v is not None}
	kwargs[page_kwarg] = page_num
	try:
		url_args = '?' + request.GET.urlencode() if request.GET else ''
		full_url = reverse(url_name, args=url_args, kwargs=kwargs) + url_args
		if page_num == 1:
			kwargs = url_kwargs.copy()
			kwargs.pop(page_kwarg, None)
			try:
				return reverse(url_name, args=url_args, kwargs=kwargs) + url_args
			except NoReverseMatch:
				pass
		return full_url
	except NoReverseMatch:
		get = request.GET.copy()
		get[page_kwarg] = page_num
		base_url = reverse(url_name, args=url_args, kwargs=url_kwargs)
		return base_url + '?' + get.urlencode()


try:
	from django_jinja import library
	from jinja2 import contextfunction

	library.global_function(contextfunction(pagination))
	library.global_function(contextfunction(pager_url))
except ImportError:
	pass
