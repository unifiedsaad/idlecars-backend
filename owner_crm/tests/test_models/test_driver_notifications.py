# -*- encoding:utf-8 -*-
from __future__ import unicode_literals

import inspect
import datetime

from django.utils import timezone
from django.test import TestCase
from django.conf import settings

from owner_crm.services import notification
from owner_crm.models import Campaign, driver_notifications
from owner_crm import factories as crm_factories

from server import factories as server_factories
from idlecars import sms_service


notification_spec = {
    'DocsApprovedNoBooking': {
        'argument': 'approved_driver',
        'sms_result': settings.WEBAPP_URL + '/#/cars',
    },
    'BaseLetterApprovedNoCheckout': {
        'argument': 'pending_booking',
        'sms_result': settings.WEBAPP_URL + '/#/account/bookings',
    },
    'FirstDocumentsReminderBooking': {
        'argument': 'pending_booking',
        'sms_result': settings.WEBAPP_URL + '/#/bookings',
    },
    'FirstDocumentsReminderDriver': {
        'argument': 'driver',
        'sms_result': settings.WEBAPP_URL + '/#/bookings',
    },
    'SecondDocumentsReminderBooking': {
        'argument': 'pending_booking',
        'sms_result': settings.WEBAPP_URL + '/#/bookings',
    },
    'SecondDocumentsReminderDriver': {
        'argument': 'driver',
        'sms_result': settings.WEBAPP_URL + '/#/bookings',
    },
    'ThirdDocumentsReminderBooking': {
        'argument': 'pending_booking',
        'sms_result': settings.WEBAPP_URL + '/#/bookings',
    },
    'ThirdDocumentsReminderDriver': {
        'argument': 'driver',
        'sms_result': settings.WEBAPP_URL + '/#/bookings',
    },
    'BookingTimedOut': {
        'argument': 'pending_booking',
        'sms_result': settings.WEBAPP_URL + '/#/cars',
    },
    'AwaitingInsuranceEmail': {
        'argument': 'requested_booking',
        'sms_result': 'pre-approved',
    },
    'InsuranceApproved': {
        'argument': 'requested_booking',
        'sms_result': 'approved',
    },
    'CheckoutReceipt': {
        'argument': 'reserved_booking',
        'sms_result': 'hold of $500 on your credit card',
    },
    'PickupConfirmation': {
        'argument': 'booked_booking',
        'sms_result': 'Success!',
    },
    'BookingCanceled': {
        'argument': 'pending_booking',
        'sms_result': 'canceled',
    },
    'PasswordReset': {
        'argument': 'password_reset',
        'sms_result': 'password',
    },
    'InsuranceRejected': {
        'argument': 'accepted_booking',
        'email_result': 'insurance',
    },
    'InsuranceFailed': {
        'argument': 'accepted_booking',
        'email_result': 'unable',
    },
    'CarRentedElsewhere': {
        'argument': 'requested_booking',
        'email_result': 'Sorry',
    },
    'PaymentReceipt': {
        'argument': 'settled_payment',
        'email_result': 'Received',
    },
    'SomeoneElseBooked': {
        'argument': 'pending_booking',
        'email_result': 'Someone else',
    },
    'PasswordResetConfirmation': {
        'argument': 'password_reset',
        'email_result': 'password',
    },
}


class DriverNotificationTest(TestCase):
    def setUp(self):
        auth_user = server_factories.AuthUser.create(first_name='Tom', last_name='Cat')

        self.driver = server_factories.Driver.create(auth_user=auth_user)
        self.complete_driver = server_factories.CompletedDriver.create()
        self.payment_method_driver = server_factories.PaymentMethodDriver.create()
        self.approved_driver = server_factories.ApprovedDriver.create()
        self.base_letter_driver = server_factories.BaseLetterDriver.create()

        car = server_factories.BookableCar.create(solo_cost=500)
        self.pending_booking = server_factories.Booking.create(car=car)
        self.reserved_booking = server_factories.ReservedBooking.create(car=car)
        self.requested_booking = server_factories.RequestedBooking.create(car=car)
        self.accepted_booking = server_factories.AcceptedBooking.create(car=car)
        self.booked_booking = server_factories.BookedBooking.create(car=car)

        self.password_reset = crm_factories.PasswordReset.create(auth_user=auth_user)

        self.settled_payment = server_factories.SettledPayment.create(
            booking=self.booked_booking,
            amount=car.solo_cost,
            invoice_start_time=timezone.now(),
            invoice_end_time=timezone.now() + datetime.timedelta(days=7),
        )

        sms_service.test_reset()


    def test_driver_notifications(self):
        from django.core import mail

        for name, obj in inspect.getmembers(driver_notifications):
            if inspect.isclass(obj):
                # make sure we know about this Notification
                self.assertTrue(name in notification_spec.keys())

                spec = notification_spec[name]
                campaign_name = 'driver_notifications.' + name
                argument = eval('self.' + notification_spec[name]['argument'])

                # check the sms if this notification is supposed to support sms
                if 'sms_result' in spec.keys():
                    crm_factories.SmsCampaign.create(name=campaign_name)
                    notification.send(campaign_name, argument)

                    self.assertEqual(len(sms_service.test_get_outbox()), 1)
                    self.assertTrue(spec['sms_result'] in sms_service.test_get_outbox()[0]['body'])
                    sms_service.test_reset()

                # check the email if this notification is supposed to support email
                if 'email_result' in spec.keys():
                    crm_factories.EmailCampaign.create(name=campaign_name)
                    notification.send(campaign_name, argument)

                    self.assertEqual(len(mail.outbox), 1)
                    self.assertTrue(
                        spec['email_result'] in mail.outbox[0].subject,
                    )
                    # manually reset outbox
                    mail.outbox = []

