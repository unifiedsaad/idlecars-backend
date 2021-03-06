# -*- encoding:utf-8 -*-
from __future__ import unicode_literals

from operator import attrgetter
from decimal import Decimal

from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator, MinLengthValidator
from django.core.validators import MaxLengthValidator
from django.contrib.auth.models import User as AuthUser


class Owner(models.Model):
    auth_users = models.ManyToManyField(AuthUser)
    company_name = models.CharField(max_length=256, blank=True)
    address1 = models.CharField(blank=True, max_length=200)
    address2 = models.CharField(blank=True, max_length=200)
    city = models.CharField(blank=True, max_length=200)
    state_code = models.CharField(blank=True, max_length=2)
    zipcode = models.CharField(blank=True, max_length=5, verbose_name='Zip Code',
        validators=[
            RegexValidator(r'^[0-9]+$', 'Only numbers are allowed in a zip code.', 'Invalid zip'),
            MinLengthValidator(5),
            MaxLengthValidator(5),
        ],
    )

    BANK_ACCOUNT_PENDING = 1
    BANK_ACCOUNT_APPROVED = 2
    BANK_ACCOUNT_DECLINED = 3
    MERCHANT_ACCOUNT_STATE = [
        (BANK_ACCOUNT_PENDING, 'Pending'),
        (BANK_ACCOUNT_APPROVED, 'Approved'),
        (BANK_ACCOUNT_DECLINED, 'Declined'),
    ]
    merchant_account_state = models.IntegerField(choices=MERCHANT_ACCOUNT_STATE, null=True)
    merchant_id = models.CharField(blank=True, max_length=200)
    service_percentage = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True, # if negotiated we use the system default
        blank=True,
        verbose_name='Negotiated service percentage',
    )
    service_percentage.short_description = 'Negotiated take rate'

    split_shift = models.NullBooleanField(verbose_name="Accepts Split Shifts", blank=True)
    RATING = [
        (0, 'Terrible'),
        (1, 'Bad'),
        (2, 'Poor'),
        (3, 'OK'),
        (4, 'Good'),
        (5, 'Excellent'),
    ]
    rating = models.IntegerField(
        choices=RATING,
        blank=True,
        null = True,
        help_text="Owner's rating based on previous experience."
    )
    notes = models.TextField(blank=True)

    sms_enabled = models.BooleanField(default=True)
    social = models.CharField(blank=True, max_length=4, verbose_name='Last 4 of SSN',
        validators=[
            RegexValidator(r'^[0-9]+$', 'Only numbers are allowed in a zip code.', 'Invalid zip'),
            MinLengthValidator(4),
            MaxLengthValidator(4),
        ],
    )
    def default_user(self):
        users = self.auth_users.all()
        if users.count() == 1:
            return users[0]
        if users.count() > 1:
            return users.order_by('first_name').first()
        return None

    def name(self):
        if self.company_name:
            return self.company_name
        sorted_users = sorted(self.auth_users.all(), key=attrgetter('last_name'))
        return ', '.join([u.get_full_name() for u in sorted_users])

    def get_user_attr(self, attrib):
        # get a value from the associated User, or return ''
        user = self.default_user()
        if user:
            return getattr(user, attrib)
        else:
            return ''

    def phone_number(self):
        return self.get_user_attr('username')

    def email(self):
        return self.get_user_attr('email')

    def first_name(self):
        return self.get_user_attr('first_name')

    @property
    def effective_service_percentage(self):
        ''' Returns the owner's negotiated rate if we negotiated one, otherwise, the default'''
        return self.service_percentage or Decimal(settings.TAKE_RATE)

    def __unicode__(self):
        name = self.name()
        return name or "Owner {}".format(self.pk)
