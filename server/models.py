from django.db import models
import model_helpers

class FleetPartner(models.Model):
    name = models.CharField(max_length=256)
    contact = models.CharField(max_length=256, blank=True)
    phone = models.CharField(max_length=256, blank=True, help_text="Comma separated")
    email = models.CharField(max_length=256, blank=True, help_text="Comma separated")

    def __unicode__(self):
        return self.name


class Driver(models.Model):
    first_name = model_helpers.StrippedCharField(max_length=30, blank=True)
    last_name = model_helpers.StrippedCharField(max_length=30, blank=True)
    phone_number = models.CharField(max_length=40, blank=True)
    email = models.CharField(blank=True, max_length=128, null=True, unique=True)
    email_verified = models.DateTimeField(null=True, blank=True)

    def get_full_name(self):
        return u"{first_name} {last_name}".format(first_name=self.first_name, last_name=self.last_name).title()

    def __unicode__(self):
        if self.email:
            return "{name} ({email})".format(name=self.get_full_name(), email=self.email)
        else:
            return "{name} ({pk})".format(name=self.get_full_name(), pk=self.pk)