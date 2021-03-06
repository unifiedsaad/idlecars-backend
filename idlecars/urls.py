# -*- encoding:utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import patterns, include, url
from django.contrib import admin


urlpatterns = patterns('',
    url(r'^auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^api/', include('server.urls', namespace='server')),
    url(r'^api/', include('owner_crm.urls', namespace='owner_crm')),
    url(r'^api/', include('addition.urls', namespace='addition')),
    url(r'^api/', include('removal.urls', namespace='removal')),

    url(r'^admin/', include('unsubscribes.urls', namespace='unsubscribes')),
    url(r'^admin/', include(admin.site.urls)),

    url(r'', include('e2e_test_setup.urls', namespace='e2e_test_setup')),
)
