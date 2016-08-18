# -*- coding: utf-8 -*-
from copy import copy

from django import template
from django.core.urlresolvers import reverse, NoReverseMatch
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe


register = template.Library()


def pagination_ctx(context, page_obj=None, page_kwarg='page'):
	page_obj = page_obj or context['page_obj']
	inner_context = copy(context)
	ctx_update = {
		'page_obj': page_obj,
		'page_kwarg': page_kwarg,
		'resolver_match': context['request'].resolver_match,
		'request': context['request'],
	}
	try:
		inner_context.update(ctx_update)
	except AttributeError:
		inner_context.vars.update(ctx_update)
	return inner_context


@register.simple_tag(takes_context=True)
def pagination(context, page_obj=None, page_kwarg='page', template_name='paginator/paginator.html'):
	rendered = render_to_string(template_name, pagination_ctx(context, page_obj, page_kwarg))
	return mark_safe(rendered)


@register.simple_tag(takes_context=True)
def pager_url(context, page_num):
	request = context['request']
	resolver_match = context['resolver_match']
	page_kwarg = context['page_kwarg']
	kwargs = {k: v for k, v in resolver_match.kwargs.items() if v is not None}
	kwargs[page_kwarg] = page_num
	try:
		url_args = '?' + request.GET.urlencode() if request.GET else ''
		full_url = reverse(resolver_match.view_name, args=resolver_match.args, kwargs=kwargs) + url_args
		if page_num == 1:
			kwargs = resolver_match.kwargs.copy()
			kwargs.pop(page_kwarg, None)
			try:
				return reverse(resolver_match.view_name, args=resolver_match.args, kwargs=kwargs) + url_args
			except NoReverseMatch:
				pass
		return full_url
	except NoReverseMatch:
		get = request.GET.copy()
		get[page_kwarg] = page_num
		base_url = reverse(resolver_match.view_name, args=resolver_match.args, kwargs=resolver_match.kwargs)
		return base_url + '?' + get.urlencode()


try:
	from django_jinja import library
	from jinja2 import contextfunction

	library.global_function(contextfunction(pagination))
	library.global_function(contextfunction(pager_url))
except ImportError:
	pass
