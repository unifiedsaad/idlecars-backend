# -*- encoding:utf-8 -*-
from __future__ import unicode_literals

import datetime
from decimal import Decimal
from factory import LazyAttribute
from factory import SubFactory, SelfAttribute, post_generation

from django.utils import timezone

from idlecars.factory_helpers import Factory, faker
from server.factories import BookableCar, ApprovedDriver, BaseLetterDriver, PaymentMethodDriver
from server.factories import Payment, PreAuthorizedPayment, SettledPayment
from server import models

class Booking(Factory):
    class Meta:
        model = 'server.Booking'

    car = SubFactory(BookableCar)
    driver = SubFactory(BaseLetterDriver)


class ReservedBooking(Booking):
    checkout_time = LazyAttribute(lambda o: timezone.now())
    end_time = LazyAttribute(lambda o: (timezone.now() + datetime.timedelta(days=7 * 6)))
    driver = SubFactory(PaymentMethodDriver)

    # checkout locks in the price and service_percentage
    weekly_rent = SelfAttribute('car.solo_cost')
    service_percentage = Decimal('0.085')

    @post_generation
    def payment(self, create, count, **kwargs):
        PreAuthorizedPayment.create(
            booking=self,
            amount=self.car.solo_deposit,
        )


class RequestedBooking(ReservedBooking):
    requested_time = LazyAttribute(lambda o: timezone.now())


class AcceptedBooking(RequestedBooking):
    approval_time = LazyAttribute(lambda o: timezone.now())


class BookedBooking(AcceptedBooking):
    pickup_time = LazyAttribute(lambda o: timezone.now())

    @post_generation
    def payment(self, create, count, **kwargs):
        for p in self.payment_set.all():
            p.status = models.Payment.HELD_IN_ESCROW
        SettledPayment.create(
            booking=self,
            amount=self.car.solo_deposit,
            invoice_start_time=LazyAttribute(lambda o: timezone.now()),
            invoice_end_time=LazyAttribute(lambda o: (timezone.now()+ datetime.timedelta(days=7)))
        )


class ReturnedBooking(BookedBooking):
    return_time = LazyAttribute(lambda o: timezone.now())


class RefundedBooking(ReturnedBooking):
    refund_time = LazyAttribute(lambda o: timezone.now())


class IncompleteBooking(Booking):
    incomplete_time = LazyAttribute(lambda o: timezone.now())
    incomplete_reason = models.Booking.REASON_CANCELED
