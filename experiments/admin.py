# -*- encoding:utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.db.models import Sum

import models


class AdminMixin:
    can_delete = False

    def has_delete_permission(self, request, obj=None):
        if self.can_delete:
            return super(ModelAdmin, self).has_delete_permission(request, obj)
        else:
            return False

    def get_object_from_request(self, request):
        object_id = request.META['PATH_INFO'].strip('/').split('/')[-1]
        try:
            object_id = int(object_id)
        except ValueError:
            return None
        return self.model.objects.get(pk=object_id)


class ModelAdmin(admin.ModelAdmin, AdminMixin):
    pass


class TabularInline(admin.TabularInline, AdminMixin):
    pass


class AlternativeInline(TabularInline):
    model = models.Alternative
    readonly_fields = (
        'participant_count',
        'conversion_count',
    )
    fields = (
        'identifier',
        'ratio',
        'participant_count',
        'conversion_count',
    )
    extra = 0
    max_num = 4


class ExperimentAdmin(ModelAdmin):
    list_display = (
        'identifier',
        'start_time',
        'end_time',
        'live',
        'default',
        'winner',
        'participant_count',
        'conversion_count',
    )
    fields = (
        'identifier',
        'description',
        'start_time',
        'end_time',
        'live',
        'default',
        'winner',
    )
    readonly_fields = (
        'live',
    )
    inlines = [
        AlternativeInline,
    ]

    def participant_count(self, instance):
        return instance.participant_count
    participant_count.admin_order_field = 'participant_count'

    def conversion_count(self, instance):
        return instance.conversion_count
    conversion_count.admin_order_field = 'conversion_count'

    def queryset(self, request):
        queryset = super(ExperimentAdmin, self).queryset(request)
        queryset = queryset.annotate(
            participant_count=Sum('alternative__participant_count'),
            conversion_count=Sum('alternative__conversion_count'),
        )
        queryset = queryset.extra(select={
            'live': "`start_time` < NOW() AND (`end_time` > NOW() OR `end_time` IS NULL)",
        })
        return queryset

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name in ('default', 'winner'):
            obj = self.get_object_from_request(request)
            conditions = {
                'experiment': obj
            }
            kwargs['queryset'] = models.Alternative.objects.filter(**conditions)
        return super(ExperimentAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    def live(self, instance):
        return instance.live
    live.admin_order_field = 'live'
    live.boolean = True
    live.short_description = "Live"


admin.site.register(models.Experiment, ExperimentAdmin)
