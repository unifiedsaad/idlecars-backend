# -*- encoding:utf-8 -*-
from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from django.template import Context
from django.template.loader import render_to_string
from django.conf import settings

from idlecars import email
from server.services import car as car_service
from owner_crm.models import Renewal

class Command(BaseCommand):
    help = 'Sends notifications to owners about the state of their cars'

    def handle(self, *args, **options):
        # TODO - optimize this query
        notifiable_cars = car_service.get_stale_within(
            60 * 2 * 24
        ).exclude(
            id__in = [r.id for r in Renewal.objects.filter(state=Renewal.STATE_PENDING)]
        )

        for car in notifiable_cars:
            for user in car.owner.user_account.all():
                renewal = Renewal.objects.create(car=car)

                # TODO - use renewal_url service
                renewal_url = 'http://{app_url}/#/cars/{car_id}/renewals/{renewal_token}'.format(
                    app_url=settings.WEBAPP_URL,
                    car_id=car.id,
                    renewal_token=renewal.token,
                )

                body = self.render_body(car)
                merge_vars = {
                    user.email: {
                        'FNAME': user.first_name or None,
                        'TEXT': body,
                        'CTA_LABEL': 'Renew Listing Now',
                        'CTA_URL': renewal_url,
                    }
                }
                email.send_async('single_cta', 'Your idlecars listing is about to expire.', merge_vars)

    def render_body(self, car):
                template_data = {
                    'CAR_NAME': car.__unicode__(),
                    'CAR_PLATE': car.plate,
                }
                context = Context(autoescape=False)
                return render_to_string("car_expiring.jade", template_data, context)
