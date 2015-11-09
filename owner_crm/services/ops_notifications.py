# # -*- encoding:utf-8 -*-
from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.conf import settings

from idlecars import email

from server import models


def documents_uploaded(driver):
    merge_vars = {
        settings.OPS_EMAIL: {
            'FNAME': 'dudes',
            'HEADLINE': 'Driver Docs uploaded!',
            'TEXT': 'Someone with the number {} uploaded all thier docs. Please see if they\'re legit'.format(
                driver.phone_number()
            ),
            'CTA_LABEL': 'Check \'em out',
            'CTA_URL': 'https://www.idlecars.com{}'.format(
                reverse('admin:server_driver_change', args=(driver.pk,))
            ),
        }
    }
    email.send_async(
        template_name='one_button_no_image',
        subject='Uploaded documents from {}'.format(driver.phone_number()),
        merge_vars=merge_vars,
    )


def payment_failed(payment):
    merge_vars = {
        settings.OPS_EMAIL: {
            'FNAME': 'peeps',
            'HEADLINE': 'A payment failed',
            'TEXT': 'the driver with phone {} had a payment fail for {}. The server response was:<br>{}'.format(
                payment.booking.driver.phone_number(),
                payment.invoice_description(),
                payment.notes,
            ),
            'CTA_LABEL': 'Payment details',
            'CTA_URL': 'https://www.idlecars.com{}'.format(
                reverse('admin:server_payment_change', args=(payment.pk,))
            ),
        }
    }
    email.send_async(
        template_name='one_button_no_image',
        subject='Payment {} for a {} failed.'.format(payment, payment.booking.car),
        merge_vars=merge_vars,
    )


def payment_job_failed(booking, message):
    merge_vars = {
        settings.OPS_EMAIL: {
            'FNAME': 'people',
            'HEADLINE': 'The payment job threw a {}'.format(message),
            'TEXT': 'the auto-payment job ran into a problem while processing payment for the booking {}'.format(
                booking,
            ),
            'CTA_LABEL': 'Booking details',
            'CTA_URL': 'https://www.idlecars.com{}'.format(
                reverse('admin:server_booking_change', args=(booking.pk,))
            ),
        }
    }
    email.send_async(
        template_name='one_button_no_image',
        subject='The payment job failed.',
        merge_vars=merge_vars,
    )


def owner_account_declined(owner, errors):
    merge_vars = {
        settings.OPS_EMAIL: {
            'FNAME': 'Dearest Admin',
            'HEADLINE': 'An owner\'s bank account was declined',
            'TEXT': '''
                {}'s bank account details were declined by the Braintree gateway.<br>
                Braintree returned the following error(s):<br>
                <ul>{}</ul>
            '''.format(owner.name(), ''.join(['<li>{}'.format(e) for e in errors])),
        }
    }
    email.send_sync(
        template_name='no_button_no_image',
        subject='{}\'s bank account was declined'.format(owner.name()),
        merge_vars=merge_vars,
    )


def new_user_message(message):
    merge_vars = {
        settings.OPS_EMAIL: {
            'FNAME': 'New user message',
            'HEADLINE': 'A new message from user {}'.format(message.first_name),
            'TEXT': '''
                User first name is: {}
                <br />
                User email is: {}
                <br />
                Message is: <br /> {}
            '''.format(message.first_name, message.email, message.message),
        }
    }
    email.send_async(
        template_name='no_button_no_image',
        subject='A new message from user {}'.format(message.first_name),
        merge_vars=merge_vars,
    )