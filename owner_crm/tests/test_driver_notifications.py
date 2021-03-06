# -*- encoding:utf-8 -*-
from __future__ import unicode_literals

from decimal import Decimal

import datetime
from freezegun import freeze_time

from django.utils import timezone
from django.test import TestCase
from django.core.management import call_command

import credit.factories
import server.factories
from idlecars import sms_service

from server.models import Booking
from server.services import driver as driver_service
from owner_crm.tests import sample_merge_vars
from owner_crm.tests.test_services import test_message
from owner_crm import factories as owner_crm_factories


''' Tests the cron job that sends delayed notifications to drivers '''
# class TestDriverDocsNotifications(TestCase):
#     @freeze_time("2014-10-10 9:55:00")
#     def _simulate_new_booking(self):
#         driver = server.factories.Driver.create()
#         return server.factories.Booking.create(driver=driver)

#     def setUp(self):
#         self.booking = self._simulate_new_booking()

#     @freeze_time("2014-10-10 11:00:00")
#     def test_docs_reminder(self):
#         driver_service.process_document_notifications()

#         test_message.verify_throttled_on_driver(
#             self.booking.driver,
#             'first_documents_reminder'
#         )

#         from django.core.mail import outbox
#         self.assertEqual(len(outbox), 1)
#         self.assertTrue(sample_merge_vars.check_template_keys(outbox))
#         self.assertEqual(
#             outbox[0].subject,
#             'Your {} is waiting on your driver documents'.format(self.booking.car.display_name())
#         )

#     @freeze_time("2014-10-10 11:00:00")
#     def test_driver_no_booking(self):
#         driver = self.booking.driver
#         self.booking.delete()
#         driver_service.process_document_notifications()
#         test_message.verify_throttled_on_driver(
#             driver,
#             'first_documents_reminder',
#         )

#         from django.core.mail import outbox
#         self.assertEqual(len(outbox), 1)
#         self.assertTrue(sample_merge_vars.check_template_keys(outbox))

#     @freeze_time("2014-10-10 11:00:00")
#     def test_no_email_twice(self):
#         driver_service.process_document_notifications()
#         test_message.verify_throttled_on_driver(
#             self.booking.driver,
#             'first_documents_reminder'
#         )

#         driver_service.process_document_notifications()

#         from django.core.mail import outbox
#         self.assertEqual(len(outbox), 1)

#     @freeze_time("2014-10-10 11:00:00")
#     def test_only_new_driver_get_reminder(self):
#         driver_service.process_document_notifications()
#         from django.core.mail import outbox
#         self.assertEqual(len(outbox), 1)

#         self._simulate_new_booking()
#         driver_service.process_document_notifications()
#         self.assertEqual(len(outbox), 2)

#     ''' check that we don't send an email to a driver who already uploaded their docs '''
#     @freeze_time("2014-10-10 11:00:00")
#     def test_docs_reminder_driver_complete(self):
#         self.booking.driver.delete()
#         server.factories.CompletedDriver.create()
#         driver_service.process_document_notifications()

#         from django.core.mail import outbox
#         self.assertEqual(len(outbox), 0)

#     def test_reminder_until_flake(self):
#         with freeze_time("2014-10-10 9:55:00"):
#             other_driver = server.factories.CompletedDriver.create()
#             other_booking = server.factories.Booking.create(driver=other_driver)

#         #TODO: time should be from settings
#         with freeze_time("2014-10-10 11:00:00"):
#             driver_service.process_document_notifications()
#         test_message.verify_throttled_on_driver(
#             self.booking.driver,
#             'first_documents_reminder'
#         )
#         with freeze_time("2014-10-11 10:00:00"):
#             driver_service.process_document_notifications()
#         test_message.verify_throttled_on_driver(
#             self.booking.driver,
#             'second_documents_reminder'
#         )
#         with freeze_time("2014-10-11 22:00:00"):
#             driver_service.process_document_notifications()
#         with freeze_time("2014-10-12 10:00:00"):
#             driver_service.process_document_notifications()
#         test_message.verify_throttled_on_driver(
#             self.booking.driver,
#             'third_documents_reminder'
#         )

#         from django.core.mail import outbox
#         '''
#         We should have sent:
#         - 3 Timed document reminders based on sign-up time for driver without docs
#         '''
#         self.assertEqual(len(outbox), 3)

'''
CreditNotifications are commented out, but left in place because All Taxi might want a referral
program in the foreseeable future.
'''
# class TestDriverCreditNotifications(TestCase):
#     @freeze_time("2014-10-10 9:55:00")
#     def setUp(self):
#         self.poor_driver = server.factories.CompletedDriver.create()

#         # rich driver signed up with a credit code, but hasn't spend the credit yet.
#         self.rich_driver = server.factories.CompletedDriver.create()
#         self.rich_driver.auth_user.customer.invitor_code = credit.factories.CreditCode.create()
#         self.rich_driver.auth_user.customer.invitor_credited = False
#         self.rich_driver.auth_user.customer.app_credit = Decimal('50.00')
#         self.rich_driver.auth_user.customer.save()

#     def test_poor_driver_no_credit_reminder(self):
#         driver_service.process_credit_notifications()

#         from django.core.mail import outbox
#         self.assertEqual(len(outbox), 3)
#         self.assertEqual(
#             outbox[0].subject,
#             'You have ${} to use towards your next rental'.format(self.rich_driver.app_credit())
#         )
#         self.assertEqual(
#             outbox[1].subject,
#             'Let us give you cash towards your rental',
#         )
#         self.assertEqual(
#             outbox[2].subject,
#             'Let us give you cash towards your rental',
#         )

#     @freeze_time("2014-10-23 8:55:00")
#     def test_reminder_delay(self):
#         driver_service.process_credit_notifications()

#         from django.core.mail import outbox
#         self.assertEqual(len(outbox), 0)

#     def test_no_email_twice(self):
#         driver_service.process_credit_notifications()
#         driver_service.process_credit_notifications()
#         driver_service.process_credit_notifications()

#         from django.core.mail import outbox
#         '''
#         1. app credit reminder to rich_driver
#         2. inactive reminder to poor driver
#         3. inactive reminder to rich driver
#         '''
#         self.assertEqual(len(outbox), 3)

#     def test_no_credit_email_with_active_booking(self):
#         server.factories.BookedBooking.create(driver=self.rich_driver)
#         driver_service.process_credit_notifications()

#         from django.core.mail import outbox
#         self.assertEqual(len(outbox), 1)

#     def test_no_credit_email_with_requested_booking(self):
#         server.factories.RequestedBooking.create(driver=self.rich_driver)
#         driver_service.process_credit_notifications()

#         from django.core.mail import outbox
#         self.assertEqual(len(outbox), 1)

#     def test_no_credit_email_with_requested_booking(self):
#         server.factories.RequestedBooking.create(driver=self.rich_driver)
#         driver_service.process_credit_notifications()

#         from django.core.mail import outbox
#         self.assertEqual(len(outbox), 1)

'''
ReferralNotifications are commented out, but left in place because All Taxi might want a referral
program in the foreseeable future.
'''
# class TestDriverReferralNotifications(TestCase):
#     @freeze_time("2014-10-10 8:55:00")
#     def setUp(self):
#         self.driver = server.factories.CompletedDriver.create()

#     def test_inactive_driver_gets_reminder(self):
#         driver_service.process_referral_notifications()

#         from django.core.mail import outbox
#         self.assertEqual(len(outbox), 1)

#         self.assertEqual(
#             outbox[0].subject,
#             'Share some Idle Cash with your friends and save on your next rental',
#         )

#     @freeze_time("2014-10-30 8:55:00")
#     def test_no_email_early(self):
#         driver_service.process_referral_notifications()

#         from django.core.mail import outbox
#         self.assertEqual(len(outbox), 0)

#     def test_incompleted_driver_no_email(self):
#         with freeze_time("2014-10-10 8:55:00"):
#             server.factories.Driver.create()

#         driver_service.process_referral_notifications()

#         from django.core.mail import outbox
#         self.assertEqual(len(outbox), 1)

#     def test_no_email_twice(self):
#         driver_service.process_referral_notifications()
#         driver_service.process_referral_notifications()

#         from django.core.mail import outbox
#         self.assertEqual(len(outbox), 1)

#     def test_processing_booking_no_email(self):
#         server.factories.ReservedBooking.create()
#         server.factories.RequestedBooking.create()
#         server.factories.AcceptedBooking.create()
#         server.factories.BookedBooking.create()

#         driver_service.process_referral_notifications()

#         from django.core.mail import outbox
#         self.assertEqual(len(outbox), 1)

#     def test_paid_driver_no_email(self):
#         server.factories.ReturnedBooking.create(driver=self.driver)
#         driver_service.process_referral_notifications()

#         from django.core.mail import outbox
#         self.assertEqual(len(outbox), 0)


# class TestDriverSignupNotifications(TestCase):
#     @freeze_time("2014-10-10 8:55:00")
#     def setUp(self):
#         self.driver = server.factories.CompletedDriver.create()

#     @freeze_time("2014-10-16 9:00:00")
#     def test_no_email_right_after_signup(self):
#         driver_service.process_signup_notifications()

#         from django.core.mail import outbox
#         self.assertEqual(len(outbox), 0)

#     @freeze_time("2014-10-17 9:00:00")
#     def test_new_driver_gets_notification(self):
#         driver_service.process_signup_notifications()

#         from django.core.mail import outbox
#         self.assertEqual(len(outbox), 1)

#         self.assertEqual(
#             outbox[0].subject,
#             'How All Taxi works',
#         )

#     @freeze_time("2014-10-17 9:00:00")
#     def test_no_email_twice(self):
#         driver_service.process_signup_notifications()
#         driver_service.process_signup_notifications()

#         from django.core.mail import outbox
#         self.assertEqual(len(outbox), 1)

#     @freeze_time("2014-10-17 9:00:00")
#     def test_no_email_with_post_pending_booking(self):
#         server.factories.RequestedBooking.create()
#         server.factories.ReturnedBooking.create()
#         server.factories.RefundedBooking.create()
#         driver_service.process_signup_notifications()

#         from django.core.mail import outbox
#         self.assertEqual(len(outbox), 1)

#     def test_signup_reminders(self):
#         with freeze_time("2014-10-17 9:00:00"):
#             driver_service.process_signup_notifications()
#         with freeze_time("2014-11-10 9:00:00"):
#             driver_service.process_signup_notifications()

#         '''
#         1. sign up first reminder.
#         2. sign up second reminder.
#         '''
#         from django.core.mail import outbox
#         self.assertEqual(len(outbox), 2)

#         self.assertEqual(
#             outbox[1].subject,
#             'Do you need a car for Uber, Lyft, or Via?',
#         )


# class TestDriverInsuranceNotifications(TestCase):
#     @freeze_time("2014-10-18 10:00:00")
#     def test_only_requested_bookings_send_emails(self):
#         with freeze_time("2014-10-17 9:00:00"):
#             good_booking = server.factories.RequestedBooking.create()
#             server.factories.Booking.create()
#             server.factories.ReturnedBooking.create()
#             server.factories.RefundedBooking.create()
#             server.factories.IncompleteBooking.create()

#         driver_service.process_insurance_notifications()

#         from django.core.mail import outbox
#         self.assertEqual(len(outbox), 1)

#         self.assertEqual(
#             outbox[0].subject,
#             'We are still working to get you on the {}’s insurance.'.format(
#                 good_booking.car.display_name()
#             )
#         )

#     @freeze_time("2014-10-18 10:00:00")
#     def test_no_email_twice(self):
#         with freeze_time("2014-10-17 9:00:00"):
#             server.factories.RequestedBooking.create()

#         driver_service.process_insurance_notifications()
#         driver_service.process_insurance_notifications()

#         from django.core.mail import outbox
#         self.assertEqual(len(outbox), 1)

#     @freeze_time("2014-10-18 8:00:00")
#     def test_no_email_early(self):
#         with freeze_time("2014-10-17 9:00:00"):
#             server.factories.RequestedBooking.create()

#         driver_service.process_insurance_notifications()

#         from django.core.mail import outbox
#         self.assertEqual(len(outbox), 0)

#     @freeze_time("2014-10-19 10:00:00")
#     def test_second_email(self):
#         with freeze_time("2014-10-17 9:00:00"):
#             server.factories.RequestedBooking.create()

#         driver_service.process_insurance_notifications()

#         from django.core.mail import outbox
#         self.assertEqual(len(outbox), 2)

#         self.assertEqual(
#             outbox[1].subject,
#             'We told the owner to get you on the insurance ASAP',
#         )
