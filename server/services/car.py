# -*- encoding:utf-8 -*-
from __future__ import unicode_literals

from server import models

from . import car_helpers, make_model_service


def filter_live(queryset):
    return car_helpers._filter_not_stale(
        car_helpers._filter_data_complete(
            car_helpers._filter_bookable(queryset)))


def filter_needs_renewal(queryset):
    return car_helpers._filter_stale(
        car_helpers._filter_data_complete(
            car_helpers._filter_bookable(queryset)))


def filter_booking_in_progress(queryset):
    return queryset.filter(car_helpers.q_booking_in_progress)


listing_queryset = filter_live(models.Car.objects.all())


def get_stale_within(minutes_until_stale):
    '''
    Returns a list of cars whose listings will expire soon
    '''
    return car_helpers._filter_stale_within(
        minutes_until_stale,
        car_helpers._filter_data_complete(
            car_helpers._filter_bookable(
                models.Car.objects.all())))


def get_image_url(car):
    return make_model_service.get_image_url(car.make_model, car.pk)


def get_min_rental_duration(car):
    duration = {
        '_01_no_min': 0,
        '_02_one_week': 7,
        '_03_two_weeks': 14,
        '_04_three_weeks': 21,
        '_05_one_month': 30,
        '_06_six_weeks': 45,
        '_07_two_months': 60,
        '_08_three_months': 90,
        '_09_four_months': 120,
        '_10_five_months': 150,
        '_11_six_months': 180,
    }
    return duration[car.min_lease]
