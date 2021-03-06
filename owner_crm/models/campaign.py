# -*- encoding:utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from idlecars import model_helpers


class Campaign(models.Model):
    created_time = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length = 255, unique=True)

    SMS_MEDIUM = 0
    EMAIL_MEDIUM = 1
    BOTH_MEDIUM = 2

    MEDIUM_CHOICES = [
        (SMS_MEDIUM, 'SMS'),
        (EMAIL_MEDIUM, 'Email'),
        (BOTH_MEDIUM, 'SMS & Email'),
    ]

    preferred_medium = models.IntegerField(
        choices=MEDIUM_CHOICES,
        default=EMAIL_MEDIUM,
    )

    notes = models.TextField(blank=True)
    notes.verbose_name = 'Description'
