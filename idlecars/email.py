# -*- encoding:utf-8 -*-
from __future__ import unicode_literals

import os

import sendgrid

from django.core.mail import EmailMessage
from django.conf import settings

from idlecars.job_queue import job_queue


def _send_now(msg):
    return msg.send()


def setup_email(template_name, subject, merge_vars):
    msg = EmailMessage(
        subject=subject,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=merge_vars.keys()
    )
    msg.template_name = template_name
    msg.merge_vars = merge_vars
    return msg


def send_async(**kwargs):
    '''
    Send an email on a different thread.
    '''
    msg = setup_email(**kwargs)
    job_queue.enqueue(_send_now, msg)


def send_sync(**kwargs):
    '''
    Send an email on this thread.
    '''
    msg = setup_email(**kwargs)
    _send_now(msg)
    return msg
