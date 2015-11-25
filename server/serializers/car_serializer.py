# -*- encoding:utf-8 -*-
from __future__ import unicode_literals

from django.utils import timezone
from rest_framework.serializers import ModelSerializer, SerializerMethodField, ChoiceField

from idlecars import client_side_routes, fields
from server.models import Car
from server.fields import CarColorField


class CarCreateSerializer(ModelSerializer):
    name = SerializerMethodField()
    state = SerializerMethodField()
    insurance = SerializerMethodField()
    listing_link = SerializerMethodField()
    available_date_display = SerializerMethodField()

    next_available_date = fields.DateArrayField(required=False, allow_null=True,)
    interior_color = CarColorField(required=False, allow_null=True,)
    exterior_color = CarColorField(required=False, allow_null=True,)
    status = ChoiceField(
        choices=Car.STATUS.keys(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Car
        fields = (
            'created_time',
            'id',
            'name',
            'plate',
            'owner',
            'base',
            'state',
            'insurance',
            'listing_link',

            'solo_cost',
            'solo_deposit',
            'status',
            'next_available_date',
            'available_date_display',
            'min_lease',
            'exterior_color',
            'interior_color',
            'last_known_mileage',
        )
        read_only_fields = (
            'id',
            'name',
            'created_time',
            'state',
            'listing_link',
            'available_date_display',
            # fields we get from the TLC
            'make_model',
            'year',
            'base',
            'insurance',
       )

    def get_name(self, obj):
        return '{} {}'.format(obj.year, obj.make_model)

    def get_state(self, obj):
        # TODO - we need to figure out what the state of the car is in some efficient way
        return 'todo'

    def get_insurance(self, obj):
        if obj.insurance:
            return obj.insurance.insurer_name
        return None

    def get_listing_link(self, obj):
        return client_side_routes.car_details_url(obj)

    def get_available_date_display(self, obj):
        if obj.status == 'busy':
            if not obj.next_available_date:
                return 'Unavailable'
            elif obj.next_available_date > timezone.now().date():
                return obj.next_available_date.strftime('%b %d')
        return 'Immediately'


class CarSerializer(CarCreateSerializer):
    class Meta(CarCreateSerializer.Meta):
        read_only_fields = CarCreateSerializer.Meta.read_only_fields + ('plate',)
