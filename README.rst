============================
Simple pagination for django
============================

Install
-------

`pip install https://github.com/mireq/django-simple-paginator.git`

Usage
-----

Settings
^^^^^^^^

.. code:: python

	INSTALLED_APPS = (
		# ...
		'django_simple_paginator',
	)

View
^^^^

.. code:: python

	# views.py

	class ObjectList(ListView):
		paginate_by = 10
		# model = ...

Template
^^^^^^^^

.. code:: html

	<!-- object_list.html -->
	{% load paginator_tags %}

	<ul>
		{% for object in object_list %}
			<li>{{ object }}</li>
		{% endfor %}
	</ul>

	<div class="pagination">{% pagination %}</div>

URLs
^^^^

.. code:: python

	# urls.py
	url(r'^object-list/(?:(?P<page>\d+)/)?$', ObjectList.as_view(), name='object_list'),


Paginator template
^^^^^^^^^^^^^^^^^^

To override default paginator template create file `paginator/paginator.html` in
directory with templates. Example `paginator.html` file is located in
`sample_project/templates/paginator` directory.
