# -*- encoding:utf-8 -*-
from __future__ import unicode_literals

import os, sys
from random import randint
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.conf import settings

from server.payment_gateways import test_braintree_params
from server import payment_gateways, factories, services, models


def _is_fake_gateway(gateway):
    return gateway is payment_gateways.get_gateway('fake')


class Command(BaseCommand):
    help = '''
    This command tests the functionality of the braintree_payments library against the
    Braintree Sandbox environment. Where possible he data we send to Braintree here is
    the data the unit tests validate against.
    '''

    def _run_test(self, test_name, gateway):
        func = getattr(self, test_name)
        func(gateway)
        print '.'

    def handle(self, *args, **options):
        # make sure braintree is set to use the sandbox!
        config = settings.BRAINTREE
        if config['environment'] != 'Sandbox':
            raise Exception('Woah! We shouldn\'t be running this on anything but Sandbox')

        gateways = [
            payment_gateways.get_gateway('braintree'),
            payment_gateways.get_gateway('fake')
        ]
        for g in gateways:
            self.owner = factories.Owner.create()
            self.driver = factories.Driver.create()

            # for some later tests
            self.car = factories.BookableCar.create(owner=self.owner)
            self.booking = factories.Booking.create(car=self.car, driver=self.driver)

            self._run_test('test_add_bank_account_failure', g)
            self._run_test('test_add_bank_account_individual', g)
            self._run_test('test_add_bank_account_business', g)
            self._run_test('test_add_payment_method', g)
            self._run_test('test_add_payment_method_error', g)
            self._run_test('test_pre_authorize_zero_dollars', g)
            self._run_test('test_void_zero_dollars', g)
            self._run_test('test_settle_zero_dollars', g)
            self._run_test('test_escrow_zero_dollars', g)
            self._run_test('test_pre_authorize_error', g)
            self._run_test('test_pre_authorize', g)
            self._run_test('test_void', g)
            self._run_test('test_settle', g)
            self._run_test('test_settle_fresh_error', g)
            self._run_test('test_settle_fresh', g)
            self._run_test('test_escrow', g)
            self._run_test('test_escrow_fresh', g)
            self._run_test('test_escrow_fresh_error', g)
            self._run_test('test_idlcars_credit_more_than_fee', g)
            self._run_test('test_idlcars_supplement_no_cash_amount', g)
            self._run_test('test_idlcars_supplement_no_cash_no_supplement', g)
            self._run_test('test_idlcars_supplement_direct_settle', g)
            self._run_test('test_idlcars_no_cash_direct_settle', g)

            # This test is not working right now. Status has to be "Settled". We can't fake that.
            # self._run_test('test_refund', g)

            self.owner.delete()
            self.driver.delete()
            self.car.delete()
            self.booking.delete()

    def test_add_bank_account_failure(self, gateway):
        success, acct, error_fields, error_msgs = gateway.link_bank_account({'funding':{}})
        if not error_fields or not error_msgs:
            print 'test_add_bank_account_failure failed for gateway {}'.format(gateway)

    def test_add_bank_account_individual(self, gateway):
        params = test_braintree_params.individual_data['to_braintree']
        success, acct, error_fields, error_msgs = gateway.link_bank_account(params)
        if not success or not acct:
            print 'test_add_bank_account_individual failed for gateway {}'.format(gateway)
            print error_msgs
        self.owner.merchant_id = acct
        self.owner.save()

    def test_add_bank_account_business(self, gateway):
        params = test_braintree_params.business_data['to_braintree']
        success, acct, error_fields, error_msgs = gateway.link_bank_account(params)
        if not success or not acct:
            print 'test_add_bank_account_business failed for gateway {}'.format(gateway)
            print error_msgs
        self.owner.merchant_id = acct
        self.owner.save()

    def test_add_payment_method(self, gateway):
        payment_method = models.PaymentMethod.objects.create(
            driver=self.driver,
        )
        success, card_info = gateway.add_payment_method(
            payment_method,
            test_braintree_params.VALID_VISA_NONCE,
        )
        if not self.driver.braintree_customer_id:
            print 'test_add_payment_method_and_pay failed to add a braintree_customer_id for {}'.format(gateway)

        if not _is_fake_gateway(gateway):
            record_count = len(payment_method.braintreerequest_set.all())
            if not record_count == 2:
                print 'test_add_payment_method saved {} records for {}'.format(record_count, gateway)

        if not success:
            print 'test_add_payment_method_and_pay failed to add payment_method for gateway {}'.format(gateway)
            return

        # save for later use in this set of tests
        token, suffix, card_type, card_logo, expiration_date, unique_number_identifier = card_info
        payment_method.gateway_token = token
        payment_method.suffix = suffix
        payment_method.card_type = card_type
        payment_method.card_logo = card_logo
        payment_method.expiration_date = expiration_date
        payment_method.unique_number_identifier = unique_number_identifier
        payment_method.save()


    def test_add_payment_method_error(self, gateway):
        # we have to fake it for the fake gatway :(
        if _is_fake_gateway(gateway):
            gateway.next_payment_method_response = (False, 'Some fake error',)

        payment_method = models.PaymentMethod.objects.create(
            driver=self.driver,
        )
        success, info = gateway.add_payment_method(
            payment_method,
            test_braintree_params.INVALID_PAYMENT_METHOD_NONCE,
        )
        if not self.driver.braintree_customer_id:
            print 'test_add_payment_method_error ALSO failed to add a braintree_customer_id in {}'.format(gateway)

        if success:
            print 'test_add_payment_method_error failed to return False in {}'.format(gateway)
        if not isinstance(info, unicode):
            print 'test_add_payment_method_error failed to return an error string in {}'.format(gateway)

    def _create_payment(self):
        '''
        This is a setUp method for a bunch of the tests below.
        '''
        car = factories.BookableCar.create(owner=self.owner)
        booking = factories.Booking.create(car=car, driver=self.driver)
        dollar_amount = '9.{}'.format(randint(10, 99)) # change so the gateway won't reject as dupe.
        return services.payment.create_payment(booking, dollar_amount)

    def _create_zero_payment(self):
        payment = self._create_payment()
        payment.amount = Decimal('0.00')
        return payment

    def _create_error_payment(self, gateway):
        # we have to handle each gateway separately :(
        if gateway is payment_gateways.get_gateway('fake'):
            next_response = (models.Payment.DECLINED, 'This transaction was declined by the fake gateway.',)
            gateway.next_payment_response.append(next_response)

        car = factories.BookableCar.create(owner=self.owner)
        booking = factories.Booking.create(car=car, driver=self.driver, service_percentage='0.000')
        return services.payment.create_payment(booking, '2078.00')

    def test_pre_authorize_zero_dollars(self, gateway):
        payment = self._create_zero_payment()
        payment = gateway.pre_authorize(payment)
        if not payment.status == models.Payment.PRE_AUTHORIZED:
            print 'test_pre_authorize_zero_dollars failed to authorize for {}'.format(gateway)

    def test_void_zero_dollars(self, gateway):
        payment = self._create_zero_payment()
        payment = gateway.pre_authorize(payment)
        payment = gateway.void(payment)
        if not payment.status == models.Payment.VOIDED:
            print 'test_void_zero_dollars failed to void for {}'.format(gateway)

    def test_settle_zero_dollars(self, gateway):
        payment = self._create_zero_payment()
        payment = gateway.pre_authorize(payment)
        payment = gateway.settle(payment)
        if not payment.status == models.Payment.SETTLED:
            print 'test_settle_zero_dollars failed to void for {}'.format(gateway)

    def test_escrow_zero_dollars(self, gateway):
        payment = self._create_zero_payment()
        payment = gateway.pre_authorize(payment)
        payment = gateway.escrow(payment)
        if not payment.status == models.Payment.HELD_IN_ESCROW:
            print 'test_escrow_zero_dollars failed to void for {}'.format(gateway)

    def test_pre_authorize(self, gateway):
        payment = self._create_payment()
        payment = gateway.pre_authorize(payment)
        if not payment.status == models.Payment.PRE_AUTHORIZED:
            print 'test_pre_authorize failed to authorize for {}'.format(gateway)
        if not payment.transaction_id:
            print 'test_pre_authorize failed to get a transaction id for {}'.format(gateway)
        if not _is_fake_gateway(gateway):
            if not len(payment.braintreerequest_set.all()) == 1:
                print 'test_pre_authorize failed to save a record for {}'.format(gateway)

    def test_pre_authorize_error(self, gateway):
        payment = self._create_error_payment(gateway)
        payment = gateway.pre_authorize(payment)
        if not payment.error_message:
            print '() test_pre_authorize_error: No error message!'.format(gateway)
        if payment.status != models.Payment.DECLINED:
            print '{} test_pre_authorize_error: Payment state != DECLINED'.format(gateway)

    def test_void(self, gateway):
        payment = self._create_payment()
        payment = gateway.pre_authorize(payment)
        payment = gateway.void(payment)
        if not payment.status == models.Payment.VOIDED:
            print 'test_void failed to void for {}'.format(gateway)
        if not _is_fake_gateway(gateway):
            if not len(payment.braintreerequest_set.all()) == 2:
                print 'test_void failed to save two records for {}'.format(gateway)

    def test_settle(self, gateway):
        payment = self._create_payment()
        payment = gateway.pre_authorize(payment)
        payment = gateway.settle(payment)
        if not payment.status == models.Payment.SETTLED:
            print 'test_settle failed to settle for {}'.format(gateway)
        if not _is_fake_gateway(gateway):
            if not len(payment.braintreerequest_set.all()) == 2:
                print 'test_settle failed to store 2 records for {}'.format(gateway)

    def test_settle_fresh_error(self, gateway):
        payment = self._create_error_payment(gateway)
        payment = gateway.settle(payment)
        if not payment.error_message:
            print '{} test_settle_error: No error message!'.format(gateway)
        if payment.status != models.Payment.DECLINED:
            print '{} test_settle_error: Payment state != DECLINED'.format(gateway)
        if not _is_fake_gateway(gateway):
            if len(payment.braintreerequest_set.all()) != 1:
                print 'test_settle_fresh_error failed to create a request record for {}'.format(gateway)

    def test_settle_fresh(self, gateway):
        ''' create a payment and go straight to SETTLED (as opposed to pre-authorizing first)'''
        payment = self._create_payment()
        payment = gateway.settle(payment)
        if not payment.status == models.Payment.SETTLED:
            print 'test_settle_fresh failed to settle for {}'.format(gateway)
        if not payment.transaction_id:
            print 'test_settle_fresh failed to get a transaction_id for {}'.format(gateway)
        if not _is_fake_gateway(gateway):
            if len(payment.braintreerequest_set.all()) != 1:
                print 'test_settle_fresh failed to create a request record for {}'.format(gateway)

    def test_escrow(self, gateway):
        payment = self._create_payment()
        payment = gateway.pre_authorize(payment)
        if payment.error_message:
            print 'test_escrow\'s pre_authorize call returned error{}'.format(payment.error_message)
        if payment.status != models.Payment.PRE_AUTHORIZED:
            print 'test_escrow\'s pre_authorize left status as {}'.format(payment.status)

        payment = gateway.escrow(payment)
        if payment.error_message:
            print 'test_escrow\'s escrow call returned error{}\n{}'.format(
                payment.error_message,
                payment.notes,
            )
        if not payment.status == models.Payment.HELD_IN_ESCROW:
            print 'test_escrow failed for {}'.format(gateway)

        if not _is_fake_gateway(gateway):
            if len(payment.braintreerequest_set.all()) != 3:
                print 'test_escrow created {} braintree_request records, not 3 for {}'.format(
                    len(payment.braintreerequest_set.all()),
                    gateway,
                )

    def test_escrow_fresh_error(self, gateway):
        payment = self._create_error_payment(gateway)
        payment = gateway.escrow(payment)
        if not payment.error_message:
            print '{} test_escrow_fresh_error: No error message!'.format(gateway)
        if payment.status != models.Payment.DECLINED:
            print '{} test_escrow_fresh_error: Payment state != DECLINED'.format(gateway)

    def _create_escrow_payment(self, gateway):
        payment = self._create_payment()
        return gateway.escrow(payment)

    def test_escrow_fresh(self, gateway):
        payment = self._create_escrow_payment(gateway)
        if not payment.status == models.Payment.HELD_IN_ESCROW:
            print 'test_escrow_fresh failed for {}'.format(gateway)

        if not _is_fake_gateway(gateway):
            if len(payment.braintreerequest_set.all()) != 1:
                print '{} test_escrow_fresh failed to create 1 braintree_payment record'.format(gateway)

    def test_refund(self, gateway):
        payment = self._create_escrow_payment(gateway)
        payment = gateway.refund(payment)
        if not payment.status == models.Payment.REFUNDED:
            print 'test_refund failed with {} for {}'.format(payment.error_message, gateway)

    def test_idlcars_credit_more_than_fee(self, gateway):
        # the total cost for this rental period is $14.XX, with a $2 service fee
        payment = services.payment.create_payment(
            self.booking,
            cash_amount = '9.{}'.format(randint(10, 99)), # change so the gateway won't reject as dupe.
            credit_amount='5.{}'.format(randint(10, 99)), # change so the gateway won't reject as dupe.
            service_fee='2.00',
        )
        if not payment.idlecars_supplement:
            print 'Unexpected bahavior of create_payment. We didn\'t generate an idlecars_supplement.'

        payment = gateway.pre_authorize(payment)
        assert payment.status == models.Payment.PRE_AUTHORIZED, 'test_idlcars_credit_more_than_fee authorization'

        payment = gateway.settle(payment)
        assert payment.status == models.Payment.SETTLED
        assert payment.error_message == ''
        assert payment.transaction_id, 'transaction_id in test_idlcars_credit_more_than_fee'
        assert payment.idlecars_transaction_id, 'idlecars_transaction_id in test_idlcars_credit_more_than_fee'

    def test_idlcars_supplement_no_cash_amount(self, gateway):
        payment = services.payment.create_payment(
            self.booking,
            cash_amount = '0.00',
            credit_amount='5.{}'.format(randint(10, 99)), # change so the gateway won't reject as dupe.
            service_fee='2.00', # we still ower the owner 3.00
        )
        assert payment.idlecars_supplement, 'idlecars_supplement in test_idlcars_supplement_no_cash_amount'

        payment = gateway.pre_authorize(payment)
        assert payment.status == models.Payment.PRE_AUTHORIZED, 'authorization at test_idlcars_supplement_no_cash_amount'

        payment = gateway.settle(payment)
        assert payment.status == models.Payment.SETTLED
        assert payment.error_message == ''
        assert not payment.transaction_id, 'should be no transaction_id if there was no cash_amount'
        assert payment.idlecars_transaction_id, 'transaction_id in test_idlcars_supplement_no_cash_amount'

    def test_idlcars_supplement_no_cash_no_supplement(self, gateway):
        payment = services.payment.create_payment(
            self.booking,
            cash_amount = '0.00',
            credit_amount='5.{}'.format(randint(10, 99)), # change so the gateway won't reject as dupe.
            service_fee='20.00', # we owe nothing!
        )
        payment = gateway.pre_authorize(payment)
        assert payment.status == models.Payment.PRE_AUTHORIZED, 'authorization at test_idlcars_supplement_no_cash_amount'

        payment = gateway.settle(payment)
        assert payment.status == models.Payment.SETTLED
        assert payment.error_message == ''
        assert not payment.idlecars_transaction_id, 'idlecars_transaction_id in test_idlcars_supplement_no_cash_no_supplement'
        assert not payment.transaction_id, 'should be no transaction_id if there was no cash_amount'

    def test_idlcars_supplement_direct_settle(self, gateway):
        payment = services.payment.create_payment(
            self.booking,
            cash_amount = '9.{}'.format(randint(10, 99)), # change so the gateway won't reject as dupe.
            credit_amount='6.{}'.format(randint(10, 99)), # change so the gateway won't reject as dupe.
            service_fee='2.00',
        )
        payment = gateway.settle(payment)
        assert payment.status == models.Payment.SETTLED
        assert payment.error_message == ''
        assert payment.transaction_id, 'transaction_id in test_idlcars_supplement_direct_settle'
        assert payment.idlecars_transaction_id, 'idlecars_transaction_id in test_idlcars_supplement_direct_settle'

    def test_idlcars_no_cash_direct_settle(self, gateway):
        payment = services.payment.create_payment(
            self.booking,
            cash_amount = '0.00',
            credit_amount='5.{}'.format(randint(10, 99)), # change so the gateway won't reject as dupe.
            service_fee='2.00',
        )
        payment = gateway.settle(payment)
        assert payment.status == models.Payment.SETTLED
        assert payment.error_message == ''
        assert not payment.transaction_id, 'transaction_id in test_idlcars_no_cash_direct_settle'
        assert payment.idlecars_transaction_id, 'idlecars_transaction_id in test_idlcars_no_cash_direct_settle'
