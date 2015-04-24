# -*- encoding:utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.core.validators import EmailValidator

from idlecars import model_helpers
from .owner import Owner


class UserAccount(models.Model):
    first_name = model_helpers.StrippedCharField(max_length=30, blank=True)
    last_name = model_helpers.StrippedCharField(max_length=30, blank=True)
    phone_number = models.CharField(max_length=40, blank=True)
    email = models.CharField(
        blank=True,
        max_length=128,
        unique=True,
        null=True,
        validators=[EmailValidator()],
    )

    # if this user is an owner, they have an owner profile
    owner = models.ForeignKey(Owner, blank=True, null=True, related_name="user_account")

    def clean(self, *args, **kwargs):
        self.email = self.email.lower().strip() or None
        super(UserAccount, self).clean(*args, **kwargs)

    def full_name(self):
        return ' '.join([n for n in [self.first_name, self.last_name] if n])

    def __unicode__(self):
        return "{name} ({contact})".format(
            name=self.full_name(),
            contact=self.email or self.phone_number or 'no contact')