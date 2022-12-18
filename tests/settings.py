# -*- coding: utf-8 -*-
INSTALLED_APPS = ['tests']
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
