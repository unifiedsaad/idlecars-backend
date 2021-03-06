# -*- encoding:utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin


class MakeModelAdmin(admin.ModelAdmin):
    search_fields = [
    'make',
    'model',
    ]

    fieldsets = (
        (None, {
            'fields': (
                'make',
                'model',
                'image_filenames',
            )
        }),
    )
