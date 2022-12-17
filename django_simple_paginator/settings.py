# -*- coding: utf-8 -*-
from django.conf import settings

PAGINATOR_ON_EACH_SIDE = getattr(settings, "PAGINATOR_ON_EACH_SIDE", 3)
PAGINATOR_ON_ENDS = getattr(settings, "PAGINATOR_ON_ENDS", 1)
PAGINATOR_TEMPLATE_NAME = getattr(settings, "PAGINATOR_TEMPLATE_NAME", 'paginator/paginator.html')
