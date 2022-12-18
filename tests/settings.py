# -*- coding: utf-8 -*-
from pathlib import Path

BASE_DIR = Path(__file__).parent

INSTALLED_APPS = ['tests', 'django_simple_paginator']
SECRET_KEY = 'secret'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
ROOT_URLCONF = 'tests.urls'
USE_TZ = False

DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.sqlite3',
		'NAME': ':memory:',
	}
}

TEMPLATES = [
	{
		'BACKEND': 'django.template.backends.django.DjangoTemplates',
		'DIRS': [BASE_DIR / 'templates'],
		'APP_DIRS': True,
		'OPTIONS': {
			'context_processors': ['django.template.context_processors.request'],
			'builtins': ['django_simple_paginator.templatetags.paginator_tags'],
		},
	},
]
