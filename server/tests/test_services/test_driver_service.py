# # -*- encoding:utf-8 -*-
from __future__ import unicode_literals

from braintree.test.nonces import Nonces

from django.utils import timezone
from django.test import TestCase
from django.conf import settings
from django.core.exceptions import ValidationError

from server.services import driver as driver_service
from server.services import booking as booking_service
from server import factories
from server.models import Booking

from owner_crm.tests import sample_merge_vars


class DriverServiceTest(TestCase):
    def setUp(self):
        self.driver = factories.Driver.create()
        self.car = factories.Car.create()


    def _set_all_docs(self):
        for doc in driver_service.doc_fields_and_names.keys():
            setattr(self.driver, doc, 'http://whatever.com')
        self.driver.save()

    def _validate_new_booking_email(self, email, booking):
        self.assertEqual(
            email.subject,
            'New Booking from {}'.format(booking.driver.phone_number())
        )
        self.assertEqual(email.merge_vars.keys()[0], settings.OPS_EMAIL)
        self.assertEqual(
            email.merge_vars[settings.OPS_EMAIL]['CTA_URL'].split('/')[-2],
            unicode(booking.pk),
        )


    def test_docs_uploaded_no_booking(self):
        self._set_all_docs()

        # we should have sent an email about the completed docs to ops
        from django.core.mail import outbox
        self.assertEqual(len(outbox), 1)
        self.assertEqual(
            outbox[0].subject,
            'Uploaded documents from {}'.format(self.driver.phone_number())
        )
        self.assertEqual(outbox[0].merge_vars.keys()[0], settings.OPS_EMAIL)
        self.assertEqual(
            outbox[0].merge_vars[settings.OPS_EMAIL]['CTA_URL'].split('/')[-2],
            unicode(self.driver.pk),
        )
        self.assertTrue(sample_merge_vars.check_template_keys(outbox))


    def test_docs_uploaded_with_pending_booking(self):
        new_booking = booking_service.create_booking(self.car, self.driver)
        self.assertEqual(new_booking.get_state(), Booking.PENDING)

        self._set_all_docs()
        from django.core.mail import outbox
        self.assertEqual(len(outbox), 2)

        # we should have sent ops an email telling them about the new booking
        self._validate_new_booking_email(outbox[0], new_booking)

        # an email to ops to let them know when the documents were all uploaded
        self.assertEqual(outbox[1].merge_vars.keys()[0], settings.OPS_EMAIL)
        self.assertEqual(
            outbox[1].subject,
            'Uploaded documents from {}'.format(self.driver.phone_number())
        )
        self.assertTrue(sample_merge_vars.check_template_keys(outbox))


    def test_base_letter_approved_no_docs_approved(self):
        self.driver = factories.CompletedDriver.create()
        self.assertEqual(self.driver.base_letter, '')
        self.driver.base_letter = 'some base letter'
        with self.assertRaises(ValidationError):
            self.driver.clean()


    def test_base_letter_approved_no_booking(self):
        self.driver = factories.CompletedDriver.create()
        self.driver.documentation_approved = True
        self.driver.base_letter = 'some base letter'
        self.driver.clean()
        self.driver.save()

        from django.core.mail import outbox
        # should be 2 emails once we setup street team email
        self.assertEqual(len(outbox), 1)

        self.assertEqual(outbox[0].merge_vars.keys()[0], self.driver.email())
        self.assertEqual(
            outbox[0].subject,
            'Welcome to idlecars, {}!'.format(self.driver.full_name())
        )


    def test_base_letter_approved_pending_booking(self):
        self.driver = factories.CompletedDriver.create()
        new_booking = booking_service.create_booking(self.car, self.driver)
        self.assertEqual(new_booking.get_state(), Booking.PENDING)

        new_booking.driver.documentation_approved = True
        new_booking.driver.base_letter = 'some base letter'
        new_booking.driver.clean()
        new_booking.driver.save()

        # still in the PENDING state because they never checked out
        self.assertEqual(new_booking.get_state(), Booking.PENDING)

        from django.core.mail import outbox
        self.assertEqual(len(outbox), 2)

        # we should have sent an email to ops telling them about the new booking
        self._validate_new_booking_email(outbox[0], new_booking)

        # and an email to the driver telling them their docs and base letter were approved
        self.assertEqual(outbox[1].merge_vars.keys()[0], new_booking.driver.email())
        self.assertEqual(
            outbox[1].subject,
            "No checkout, {}!".format(self.driver.full_name())
        )


    def test_base_letter_approved_reserved_booking(self):
        self.driver = factories.PaymentMethodDriver.create()
        new_booking = factories.ReservedBooking.create(driver=self.driver)
        self.assertEqual(new_booking.get_state(), Booking.RESERVED)
        self.assertFalse(self.driver.documentation_approved)
        self.assertFalse(self.driver.base_letter_rejected)
        self.assertEqual(self.driver.base_letter, '')

        # THEN the documents are approved
        new_booking.driver.documentation_approved = True
        new_booking.driver.base_letter = 'some base letter'
        new_booking.driver.clean()
        new_booking.driver.save()

        from django.core.mail import outbox
        self.assertEqual(len(outbox), 1)

        # we should have sent an email to the owner asking them to add the driver to the insurance
        self.assertEqual(outbox[0].merge_vars.keys()[0], new_booking.car.owner.email())
        self.assertEqual(
            outbox[0].subject,
            'A driver has booked your {}.'.format(new_booking.car.display_name())
        )
        self.assertTrue(sample_merge_vars.check_template_keys(outbox))


    def test_base_letter_rejected(self):
        pass
