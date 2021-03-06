# -*- encoding:utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings


def password_reset(password_reset):
    parts = (settings.OWNER_APP_URL, '#', 'reset_password', password_reset.token)
    return '/'.join(parts)

def owner_app_url():
    return settings.OWNER_APP_URL

def car_details_url(car):
    parts = (settings.OWNER_APP_URL, '#', 'cars', unicode(car.id))
    return '/'.join(parts)

def owner_account_url():
    parts = (settings.OWNER_APP_URL, '#', 'account')
    return '/'.join(parts)
