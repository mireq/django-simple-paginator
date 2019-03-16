# -*- coding: utf-8 -*-
from django.conf import settings

PAGINATOR_INNER_COUNT = getattr(settings, "PAGINATOR_INNER_COUNT", 3)
PAGINATOR_OUTER_COUNT = getattr(settings, "PAGINATOR_OUTER_COUNT", 1)
PAGINATOR_TEMPLATE_NAME = getattr(settings, "PAGINATOR_TEMPLATE_NAME", 'paginator/paginator.html')
