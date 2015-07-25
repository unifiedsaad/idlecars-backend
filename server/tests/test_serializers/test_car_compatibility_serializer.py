# -*- encoding:utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase

from server import serializers, factories, models

class TestCarCompatibilitySerializer(TestCase):
    def setUp(self):
        factories.RideshareProviderFactory.create(friendly_id='uber_x', name='TacoRide')

    def test_serializer(self):
        car = factories.Car.create()
        car_compatibility = models.CarCompatibility(car)
        serialized = serializers.CarCompatibilitySerializer(car_compatibility)
        self.assertEqual(serialized.data['uber_x'], 'TacoRide')
