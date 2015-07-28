# -*- encoding:utf-8 -*-
from __future__ import unicode_literals

class CarCompatibility(object):
    def __init__(self, car):
        self.car = car
        self._compatible_flavors = None

    def uber_x(self):
        if self.car.year > 2009:
            return self._compatible_flavor_name('uber_x')

    def _compatible_flavor_name(self, friendly_id):
        if not self._compatible_flavors:
            self._compatible_flavors = self._get_compatible_flavors()

        return self._compatible_flavors.get(friendly_id)

    def _get_compatible_flavors(self):
        return {
            flavor.friendly_id: flavor.name for flavor in self.car.make_model.rideshareflavor_set.all()
        }
