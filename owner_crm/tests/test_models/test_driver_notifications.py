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
from idlecars import factories as idlecars_factories
from server import factories as server_factories
from idlecars import sms_service, fields


class DriverNotificationTest(TestCase):
    def setUp(self):
        auth_user = idlecars_factories.AuthUser.create(first_name='Tom', last_name='Cat')

        self.driver = server_factories.Driver.create(auth_user=auth_user)
        self.complete_driver = server_factories.CompletedDriver.create()
        self.payment_method_driver = server_factories.CompletedDriver.create()
        self.approved_driver = server_factories.CompletedDriver.create()
        self.base_letter_driver = server_factories.CompletedDriver.create()

        car = server_factories.BookableCar.create(weekly_rent=500)
        self.pending_booking = server_factories.Booking.create(car=car)
        self.requested_booking = server_factories.RequestedBooking.create(car=car)
        self.returned_booking = server_factories.ReturnedBooking.create(car=car)
        self.refunded_booking = server_factories.RefundedBooking.create(car=car)
        self.password_reset = crm_factories.PasswordReset.create(auth_user=auth_user)

        sms_service.test_reset()

        self.notification_spec = {
            'SignupConfirmation': {
                'argument': 'driver',
                'email_result': 'Welcome to All Taxi',
            },
            'SignupFirstReminder': {
                'argument': 'driver',
                'email_result': 'How All Taxi works',
            },
            'SignupSecondReminder': {
                'argument': 'driver',
                'email_result': 'Uber',
            },
            'DocsApprovedNoBooking': {
                'argument': 'approved_driver',
                'email_result': 'Welcome to All Taxi',
            },
            'FirstDocumentsReminderBooking': {
                'argument': 'pending_booking',
                'email_result': self.pending_booking.car.display_name(),
            },
            'FirstDocumentsReminderDriver': {
                'argument': 'driver',
                'email_result': 'Submit your documents',
            },
            'SecondDocumentsReminderBooking': {
                'argument': 'pending_booking',
                'email_result': self.pending_booking.car.display_name(),
            },
            'SecondDocumentsReminderDriver': {
                'argument': 'driver',
                'email_result': 'Are you ready',
            },
            'ThirdDocumentsReminderBooking': {
                'argument': 'pending_booking',
                'email_result': 'submit your driver documents',
            },
            'ThirdDocumentsReminderDriver': {
                'argument': 'driver',
                'email_result': 'Are you ready',
            },
            'BookingTimedOut': {
                'argument': 'pending_booking',
                'email_result': self.pending_booking.car.display_name(),
            },
            'AwaitingInsuranceEmail': {
                'argument': 'requested_booking',
                'email_result': 'submitted',
            },
            'FirstInsuranceNotification': {
                'argument': 'requested_booking',
                'email_result': 'insurance',
            },
            'SecondInsuranceNotification': {
                'argument': 'requested_booking',
                'email_result': 'insurance',
            },
            'InsuranceApproved': {
                'argument': 'requested_booking',
                'email_result': self.requested_booking.car.display_name(),
            },
            'CheckoutReceipt': {
                'argument': 'requested_booking',
                'email_result': 'Your {} was successfully reserved'.format(
                        self.requested_booking.car.display_name(),
                    ),
            },
            'BookingCanceled': {
                'argument': 'pending_booking',
                'email_result': 'canceled',
            },
            'DriverRemoved': {
                'argument': 'refunded_booking',
                'email_result': self.refunded_booking.car.display_name(),
            },
            'PasswordReset': {
                'argument': 'password_reset',
                'email_result': 'Reset your All Taxi password',
            },
            'InvitorReceivedCredit': {
                'argument': 'approved_driver',
                'email_result': 'credit',
            },
            'UseYourCredit': {
                'argument': 'approved_driver',
                'email_result': 'next rental',
            },
            'SignupCredit': {
                'argument': 'driver',
                'email_result': 'Idlecars rental',
            },
            'ReferFriends': {
                'argument': 'approved_driver',
                'email_result': 'refer',
            },
            'InactiveCredit': {
                'argument': 'approved_driver',
                'additional_args': '50.00',
                'email_result': 'cash',
            },
            'InactiveReferral': {
                'argument': 'approved_driver',
                'email_result': 'Share',
            },
            'InsuranceRejected': {
                'argument': 'requested_booking',
                'email_result': 'You couldn\'t be added to the car you wanted',
            },
            'InsuranceFailed': {
                'argument': 'requested_booking',
                'email_result': 'unable',
            },
            'CarRentedElsewhere': {
                'argument': 'requested_booking',
                'email_result': 'Sorry',
            },
            'SomeoneElseBooked': {
                'argument': 'pending_booking',
                'email_result': 'Someone else',
            },
            'PasswordResetConfirmation': {
                'argument': 'password_reset',
                'email_result': 'Your All Taxi password has been set.',
            },
        }

    def test_driver_notifications(self):
        from django.core import mail

        for name, obj in inspect.getmembers(driver_notifications):
            if inspect.isclass(obj):
                # make sure we know about this Notification
                self.assertTrue(name in self.notification_spec.keys())

                spec = self.notification_spec[name]
                campaign_name = 'driver_notifications.' + name
                campaign = crm_factories.Campaign.create(name=campaign_name)
                argument = eval('self.' + spec['argument'])

                # check the sms if this notification is supposed to support sms
                if 'sms_result' in spec.keys():
                    campaign.preferred_medium = Campaign.SMS_MEDIUM
                    campaign.save()

                    if 'additional_args' in spec.keys():
                        notification.send(campaign_name, argument, spec['additional_args'])
                    else:
                        notification.send(campaign_name, argument)

                    # print campaign_name
                    self.assertEqual(len(sms_service.test_get_outbox()), 1)
                    self.assertTrue(spec['sms_result'] in sms_service.test_get_outbox()[0]['body'])
                    sms_service.test_reset()

                # check the email if this notification is supposed to support email
                if 'email_result' in spec.keys():
                    campaign.preferred_medium = Campaign.EMAIL_MEDIUM
                    campaign.save()

                    if 'additional_args' in spec.keys():
                        notification.send(campaign_name, argument, spec['additional_args'])
                    else:
                        notification.send(campaign_name, argument)

                    self.assertEqual(len(mail.outbox), 1)
                    # print mail.outbox[0].subject + ' --------------- ' + campaign_name
                    self.assertTrue(spec['email_result'] in mail.outbox[0].subject)

                    # manually reset outbox
                    mail.outbox = []
