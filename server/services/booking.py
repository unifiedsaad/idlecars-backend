# # -*- encoding:utf-8 -*-
from __future__ import unicode_literals

import datetime

from django.utils import timezone
from django.conf import settings
from django.db import DatabaseError, transaction

from owner_crm.services import notification

from server.models import Booking, Payment
from . import invoice_service
from . import payment as payment_service
from server.services import ServiceError


CANCEL_ERROR = 'Sorry, your rental can\'t be canceled at this time. Please call All Taxi Management at ' + settings.ALLTAXI_PHONE_NUMBER
INSURANCE_APPROVAL_ERROR = 'Sorry, your rental can\'t be approved at this time.'
INSURANCE_REJECT_ERROR = 'Sorry, your rental can\'t be rejected at this time.'
PICKUP_ERROR = 'Sorry, your rental can\'t be picked up at this time.'
RETURN_ERROR = 'Sorry, something went wrong. Please reload the page and try again.'
RETURN_CONFIRM_ERROR = 'The driver must indicate that they have returned the car before you can return the deposit.'
UNAVAILABLE_CAR_ERROR = 'Sorry, that car is unavailable right now. Here are other cars you can rent.'


def filter_pending(booking_queryset):
    return booking_queryset.filter(
        requested_time__isnull=True,
        approval_time__isnull=True,
        incomplete_time__isnull=True,
    )

def filter_requested(booking_queryset):
    return booking_queryset.filter(
        requested_time__isnull=False,
        approval_time__isnull=True,
        incomplete_time__isnull=True,
    )

def filter_returned(booking_queryset):
    return booking_queryset.filter(
        approval_time__isnull=False,
        refund_time__isnull=True,
        incomplete_time__isnull=True,
    )

# TODO: unit test this
def filter_refunded(booking_queryset):
    return booking_queryset.filter(
        incomplete_time__isnull=True,
        refund_time__isnull=False,
    )


# TODO: unit test this
def filter_incomplete(booking_queryset):
    return booking_queryset.filter(
        incomplete_time__isnull=False,
    )


def post_pending_bookings(booking_queryset):
    requested_bookings = filter_requested(booking_queryset)
    returned_bookings = filter_returned(booking_queryset)
    refunded_bookings = filter_refunded(booking_queryset)
    return requested_bookings | returned_bookings | refunded_bookings


def is_visible(booking):
    ''' Can this booking be seen in the Driver app '''
    return not booking.refund_time and not booking.incomplete_time


def filter_visible(booking_queryset):
    ''' Can this booking be seen in the Driver app '''
    return booking_queryset.filter(refund_time__isnull=True, incomplete_time__isnull=True)


def on_car_missed(car):
    # cancel other bookings on this car when the owner says the car is no longer available.
    conflicting_bookings = []
    conflicting_bookings.extend(filter_pending(Booking.objects.filter(car=car)))
    conflicting_bookings.extend(filter_requested(Booking.objects.filter(car=car)))
    for conflicting_booking in conflicting_bookings:
        _make_booking_incomplete(conflicting_booking, Booking.REASON_MISSED)


def on_all_docs_uploaded(driver):
    if not filter_pending(Booking.objects.filter(driver=driver)):
        notification.send('driver_notifications.DocsApprovedNoBooking', driver)

    reserved_bookings = filter_pending(Booking.objects.filter(driver=driver))
    for booking in reserved_bookings:
        request_insurance(booking)


def someone_else_booked(booking):
    if booking.driver.all_docs_uploaded():
        return _make_booking_incomplete(booking, Booking.REASON_ANOTHER_BOOKED_CC)
    else:
        return _make_booking_incomplete(booking, Booking.REASON_ANOTHER_BOOKED_DOCS)


def request_insurance(booking):
    ''' When a booking is complete, we send emails to owner to approve'''
    booking.requested_time = timezone.now()
    booking.save()

    # cancel other conflicting in-progress bookings and notify those drivers
    conflicting_pending_bookings = filter_pending(Booking.objects.filter(car=booking.car))
    for conflicting_booking in conflicting_pending_bookings:
        conflicting_booking = someone_else_booked(conflicting_booking)

    if booking.driver.address_proof_image:
        notification.send('owner_notifications.NewBookingEmail', booking)
    else:
        notification.send('owner_notifications.NewBookingEmailNoMVR', booking)
    notification.send('driver_notifications.AwaitingInsuranceEmail', booking)

    return booking


def on_insurance_approved(booking):
    notification.send('ops_notifications.InsuranceApproved', booking)
    pass


def create_booking(car, driver):
    '''
    Creates a new booking
    arguments
    - car: an existing car object
    - driver: the driver making the booking
    '''
    booking = Booking.objects.create(car=car, driver=driver,)

    if driver.all_docs_uploaded():
        booking = request_insurance(booking)

    return booking


def can_cancel(booking):
    return not booking.approval_time


def cancel(booking):
    if not can_cancel(booking):
        raise ServiceError(CANCEL_ERROR)
    _make_booking_incomplete(booking, Booking.REASON_CANCELED)


def _make_booking_incomplete(booking, reason):
    original_booking_state = booking.get_state()
    booking.incomplete_time = timezone.now()
    booking.incomplete_reason = reason
    on_incomplete(booking, original_booking_state)
    booking.save()
    return booking


def on_incomplete(booking, original_booking_state):
    ''' Called any time a booking is set to incomplete'''
    invoice_service.void_all_payments(booking)

    # let our customers know what happened
    reason = booking.incomplete_reason
    if reason == Booking.REASON_CANCELED:
        notification.send('driver_notifications.BookingCanceled', booking)
        if Booking.REQUESTED == original_booking_state:
            notification.send('owner_notifications.BookingCanceled', booking)
    elif reason == Booking.REASON_OWNER_TOO_SLOW:
        pass
        # notification.send('owner_notifications.InsuranceTooSlow', booking)
        # notification.send('driver_notifications.InsuranceFailed', booking)
        # elif reason in [Booking.REASON_DRIVER_TOO_SLOW_DOCS, Booking.REASON_DRIVER_TOO_SLOW_CC]:
        # notification.send('driver_notifications.BookingTimedOut', booking)
    elif reason in [Booking.REASON_ANOTHER_BOOKED_DOCS, Booking.REASON_ANOTHER_BOOKED_CC]:
        notification.send('driver_notifications.SomeoneElseBooked', booking)
    elif reason in [
        Booking.REASON_OWNER_REJECTED,
        Booking.REASON_INSURANCE_REJECTED_AGE,
        Booking.REASON_INSURANCE_REJECTED_EXP,
        Booking.REASON_INSURANCE_REJECTED_PTS,
    ]:
        notification.send('driver_notifications.InsuranceRejected', booking)
    elif reason == Booking.REASON_DRIVER_REJECTED:
        notification.send('owner_notifications.DriverRejected', booking)
    elif reason == Booking.REASON_MISSED:
        notification.send('driver_notifications.CarRentedElsewhere', booking)


def estimate_next_rent_payment(booking):
    '''
    Returns a tuple of (service_fee, rent_amount, app_credit_amount, start_time, end_time), based
    on an estimated pickup time
    '''
    assert not booking.pickup_time

    estimated_pickup_time = estimate_pickup_time(booking)
    estimated_end_time = calculate_end_time(booking, estimated_pickup_time)
    return invoice_service.calculate_next_rent_payment(
        booking,
        estimated_pickup_time,
        estimated_end_time
    )


def is_requested(booking):
    return booking.get_state() == Booking.REQUESTED


def approve(booking):
    if not is_requested(booking):
        raise ServiceError(INSURANCE_APPROVAL_ERROR)
    booking.approval_time = timezone.now()
    booking.save()
    on_insurance_approved(booking)


def reject(booking):
    if not is_requested(booking):
        raise ServiceError(INSURANCE_REJECT_ERROR)
    _make_booking_incomplete(booking, Booking.REASON_OWNER_REJECTED)


def pickup(booking):
    '''
    Warning: this method might change the booking even if it's unsuccessful. Caller should
    reload the object before relying on its data.
    '''
    with transaction.atomic():
        try:
            # we have to re-fetch the booking so we can make sure we have a lock on the db row.
            safe_booking = Booking.objects.select_for_update(nowait=True).filter(pk=booking.pk).get()
            booking.pickup_time=timezone.now().replace(microsecond=0)

            # this acts as a flag to prevent re-entry
            safe_booking.pickup_time=booking.pickup_time
            safe_booking.save()

        except DatabaseError:
            # if the row is already locked, bail but don't show the user an error.
            raise ServiceError('')

    try:
        # NB: we don't save() the booking unless successful...
        booking.end_time = calculate_end_time(booking, booking.pickup_time)

        deposit_payment = invoice_service.find_deposit_payment(booking) or \
            invoice_service.make_deposit_payment(booking)

        if deposit_payment.error_message:
            raise ServiceError(deposit_payment.error_message)

        # pre-authorize the payment for the first week's rent
        rent_payment = invoice_service.create_next_rent_payment(booking)
        rent_payment = payment_service.pre_authorize(rent_payment)
        if rent_payment.status != Payment.PRE_AUTHORIZED:
            raise ServiceError(rent_payment.error_message)

        # hold the deposit in escrow for the duration of the rental
        if deposit_payment.status is not Payment.HELD_IN_ESCROW:
            deposit_payment = payment_service.escrow(deposit_payment)
        if deposit_payment.status != Payment.HELD_IN_ESCROW:
            raise ServiceError(deposit_payment.error_message)

        # take payment for the first week's rent
        rent_payment = payment_service.settle(rent_payment)
        if rent_payment.status != Payment.SETTLED:
            raise ServiceError(rent_payment.error_message)

    except ServiceError as e:
        # unlock the row and allow pickup() to be attempted again
        Booking.objects.filter(pk=booking.pk).update(pickup_time=None)
        raise e

    booking.save()

    return booking


def return_confirm(booking):
    '''
    The owner can confirm that the car was returned and can refund the deposit.
    '''
    if not booking or booking.get_state() != Booking.RETURNED:
        raise ServiceError(RETURN_CONFIRM_ERROR)

    booking.refund_time = timezone.now()
    on_driver_removed(booking)
    booking.save()


def on_driver_removed(booking):
    notification.send('ops_notifications.DriverRemoved', booking)


def start_time_display(booking):
    def _format_date(date):
        return date.strftime('%b %d')

    if booking.requested_time:
        return _format_date(booking.requested_time)
    else:
        return "Not requested"


def first_valid_end_time(booking):
    '''
    Returns a typle (ealiest legal end time, if the min_rental was limiting the 1st value)
    '''
    notice = timezone.now() + datetime.timedelta(days=7)
    min_rental = datetime.timedelta(days=booking.car.minimum_rental_days() or 1)
    min_rental_end = booking.pickup_time or estimate_pickup_time(booking) + min_rental
    return max(notice, min_rental_end), min_rental_end > notice


def estimate_pickup_time(booking):
    assert not booking.pickup_time  # if there's a pickup_time, then start_time is known.
    if booking.approval_time:
        pickup_date = booking.approval_time + datetime.timedelta(days=1)
    else:
        pickup_date = timezone.now() + datetime.timedelta(days=2)

    now = timezone.now()
    pickup_time = pickup_date.replace(hour=now.hour, minute=now.minute, second=now.second)
    return pickup_time


def estimate_end_time(booking):
    assert not booking.pickup_time
    return calculate_end_time(booking, estimate_pickup_time(booking))


def calculate_end_time(booking, pickup_time):
    ''' calculate the end_time based on pickup_time. '''
    if booking.end_time:
        # booking.end_time may have been set through the API. If so, it had no time of day.
        return booking.end_time.replace(
            hour=pickup_time.hour,
            minute=pickup_time.minute,
            second=pickup_time.second,
        )
    else:
        min_duration = booking.car.minimum_rental_days() or 1
        return pickup_time + datetime.timedelta(days=min_duration)


# TODO: move this up to the API
def set_end_time(booking, end_time):
    return booking
    # if booking.end_time:
    #     booking.end_time = booking.end_time.replace(
    #         year=end_time.year,
    #         month=end_time.month,
    #         day=end_time.day,
    #     )
    #     if booking.get_state() == Booking.ACTIVE:
    #         notification.send('owner_notifications.ExtendedRental', booking)
    # else:
    #     booking.end_time = end_time

    # booking.save()
    # return booking


def on_authorized_mvr(booking):
    # we need to apprise all taxi about this booking
    pass
