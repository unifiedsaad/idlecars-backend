# -*- encoding:utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from server import models
from server.admin.booking import BookingInline


class DriverAdmin(admin.ModelAdmin):
    list_display = [
        'full_name',
        'documentation_complete',
        'booking_count',
    ]
    list_filter = [
        'documentation_complete'
    ]
    search_fields = [
        'user_account__first_name',
        'user_account__last_name',
        'user_account__phone_number',
        'user_account__email',
    ]
    fieldsets = (
        (None, {
            'fields': (
                ('full_name'),
                ('phone_number'),
                ('email'),
            )
        }),
        ('Documentation', {
            'fields': (
                ('documentation_complete'),
                ('dmv_license'),
                ('fhv_license'),
                ('dd_cert'),
                ('proof_of_address'),
            )
        }),
    )
    readonly_fields = [
        'full_name',
        'email',
        'phone_number',
        'dmv_license',
        'fhv_license',
        'dd_cert',
        'proof_of_address',
    ]
    inlines = [
        BookingInline,
    ]

    def booking_count(self, instance):
        return models.Booking.objects.filter(driver=instance).count()

    def dmv_license(self, instance): return 'placeholder'
    def fhv_license(self, instance): return 'placeholder'
    def dd_cert(self, instance): return 'placeholder'
    def proof_of_address(self, instance): return 'placeholder'
