# -*- encoding:utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from idlecars.admin_helpers import link
from server import models
from server.services import payment as payment_service


class PaymentAdmin(admin.ModelAdmin):
    can_delete = False
    fieldsets = (
        (None, {
            'fields': (
                ('invoice_description', 'booking_link',),
                ('created_time', 'amount', 'service_fee', 'payment_method',),
                ('status', 'error_message',),
                ('gateway_link',),
            )
        }),
    )

    readonly_fields = [
        'created_time',
        'booking_link',
        'invoice_description',
        'amount',
        'service_fee',
        'payment_method',
        'status',
        'error_message',
        'gateway_link',
    ]
    list_display = ('created_time', 'invoice_description', 'booking_link', 'amount', 'status')
    date_hierarchy = 'created_time'
    search_fields = [
        'booking__driver__first_name',
        'booking__driver__last_name',
        'booking__car__plate',
        'transaction_id',
    ]
    list_filter = ['status']

    def booking_link(self, instance):
        return link(instance.booking)
    booking_link.short_description = 'Booking'

    def gateway_link(self, instance):
        return payment_service.details_link(instance)
    gateway_link.short_description = 'Gateway link'

    def queryset(self, request):
        return super(PaymentAdmin, self).queryset(request).prefetch_related(
            'booking',
            'booking__driver',
            'booking__car',
            'booking__payment_method',
        )


class PaymentInline(admin.TabularInline):
    model = models.Payment
    verbose_name = 'Payments'
    extra = 0
    can_delete = False
    fields = ['time_link', 'invoice_description', 'amount', 'status', 'payment_method']
    readonly_fields = ['time_link', 'invoice_description', 'amount', 'status', 'payment_method']
    def time_link(self, instance):
        return link(instance, instance.created_time.strftime("%b %d, %Y %H:%M:%S"))
    def gateway_link(self, instance):
        return payment_service.details_link(instance)
    gateway_link.short_description = 'Gateway link'
