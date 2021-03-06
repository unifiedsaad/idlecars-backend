# -*- encoding:utf-8 -*-
from __future__ import unicode_literals

"""
WSGI config for idlecars project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application
from dj_static import Cling

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "idlecars.settings")

application = Cling(get_wsgi_application())
