# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url

from . import views


urlpatterns = [
	url(r'^$', views.home_view, name='home'),
	url(r'^default/(?:(?P<page>\d+)/)?$', views.default_paginator_view, name='default_paginator'),
	url(r'^large/(?:(?P<page>\d+)/)?$', views.large_paginator_view, name='large_paginator'),
]
