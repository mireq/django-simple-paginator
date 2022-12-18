# -*- coding: utf-8 -*-
from django import template
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.urls import reverse, NoReverseMatch
from django.utils.encoding import force_str
from django.utils.safestring import mark_safe

from ..settings import PAGINATOR_ON_EACH_SIDE, PAGINATOR_ON_ENDS, PAGINATOR_TEMPLATE_NAME


register = template.Library()


def assign_range_to_page_obj(page_obj, on_each_side, on_ends):
	page_range = page_obj.paginator.get_elided_page_range(page_obj.number, on_each_side=on_each_side, on_ends=on_ends)
	page_obj.page_range = [None if page == Paginator.ELLIPSIS else page for page in page_range]
	return page_obj


def pagination_ctx(context, page_obj, page_kwarg, on_each_side, on_ends, extra_context, url_name, url_args, url_kwargs): # pylint: disable=too-many-arguments
	if page_obj is None or page_obj == '':
		page_obj = context['page_obj']
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
	page_obj = assign_range_to_page_obj(page_obj, on_each_side, on_ends)
	ctx_update = {
		'page_obj': page_obj,
		'page_range': page_obj.page_range,
		'page_kwarg': page_kwarg,
		'url_name': url_name,
		'url_args': url_args,
		'url_kwargs': url_kwargs,
	}
	inner_context.update(ctx_update)
	if extra_context is not None:
		inner_context.update(extra_context)
	return inner_context


@register.simple_tag(takes_context=True)
def pagination(context, page_obj=None, page_kwarg='page', template_name=PAGINATOR_TEMPLATE_NAME, on_each_side=PAGINATOR_ON_EACH_SIDE, on_ends=PAGINATOR_ON_ENDS, extra_context=None, url_name=None, *url_args, **url_kwargs): # pylint: disable=too-many-arguments
	rendered = render_to_string(template_name, pagination_ctx(context, page_obj, page_kwarg, on_each_side, on_ends, extra_context, url_name, url_args, url_kwargs))
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
		get_params = '?' + request.GET.urlencode() if request.GET else ''
		full_url = reverse(url_name, args=url_args, kwargs=kwargs) + get_params
		if page_num == 1:
			kwargs = url_kwargs.copy()
			kwargs.pop(page_kwarg, None)
			try:
				return reverse(url_name, args=url_args, kwargs=kwargs) + get_params
			except NoReverseMatch:
				pass
		return full_url
	except NoReverseMatch:
		get = request.GET.copy()
		get[page_kwarg] = force_str(page_num)
		base_url = reverse(url_name, args=url_args, kwargs=url_kwargs)
		return base_url + '?' + get.urlencode()


try:
	from django_jinja import library
	try:
		from jinja2 import pass_context
	except ImportError: # pragma: no cover
		from jinja2 import contextfunction as pass_context # pragma: no cover

	library.global_function(pass_context(pagination))
	library.global_function(pass_context(pager_url))
except ImportError: # pragma: no cover
	pass # pragma: no cover
