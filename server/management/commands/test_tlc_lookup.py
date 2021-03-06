# -*- encoding:utf-8 -*-
from __future__ import unicode_literals

from django.core.management.base import BaseCommand

from server import models, factories
from server.services import tlc_data_service


class Command(BaseCommand):
    help = '''
    Before running this test, change the TLC_DATA_IMPLEMENTATION settings to 'Socrata'

    This command tests the tlc_data_service. This command should use NO database connection,
    so *should* leave no permanent trace and *should* be safe to run in any environment. it
    relies on a network connection.
    '''
    def handle(self, *args, **options):
            self._run_test('test_lookup_car')

    def _run_test(self, test_name):
        func = getattr(self, test_name)
        func()
        print '.'

    def test_lookup_car(self):
        new_car = factories.Car.build(plate=tlc_data_service._get_real_medallion())
        tlc_data_service.lookup_car_data(new_car)
        assert(new_car.registrant_name != None)
