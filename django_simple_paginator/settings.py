# -*- coding: utf-8 -*-
from django.conf import settings

PAGINATOR_INNER_COUNT = getattr(settings, "PAGINATOR_INNER_COUNT", 3)
PAGINATOR_OUTER_COUNT = getattr(settings, "PAGINATOR_OUTER_COUNT", 1)
