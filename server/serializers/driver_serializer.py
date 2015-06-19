# -*- encoding:utf-8 -*-
from __future__ import unicode_literals

from django.contrib import auth
from django.core.exceptions import PermissionDenied

from rest_framework.serializers import ModelSerializer, CharField, EmailField, ValidationError

from server import models


class DriverSerializer(ModelSerializer):
    # we must add fields that are mapped to auth_user
    phone_number = CharField(max_length=30)
    password = CharField(max_length=128, write_only=True)
    email = EmailField(required=False)
    first_name = CharField(max_length=30, required=False)
    last_name = CharField(max_length=30, required=False)

    class Meta:
        model = models.Driver
        fields = (
            'id',
            'driver_license_image',
            'fhv_license_image',
            'address_proof_image',
            'defensive_cert_image',
            'all_docs_uploaded',

            # stuff from auth_user
            'phone_number',
            'password',
            'email',
            'first_name',
            'last_name',
        )
        extra_kwargs={'password': {'write_only': True}}
        read_only_fields = ('id', 'all_docs_uploaded',)

    def create(self, validated_data):
        phone_number = validated_data.get('phone_number')
        try:
            auth_user = auth.models.User.objects.get(username=phone_number)
            # TODO(JP): allow driver creation if you are authrorized as this user
            raise ValidationError("This phone number already has a user.")
        except auth.models.User.DoesNotExist:
            password = validated_data.get('password')
            auth_user = auth.models.User.objects.create_user(
                username=phone_number,
                password=password,
            )
        new_driver = models.Driver.objects.create(auth_user=auth_user)
        return new_driver

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            raise PermissionDenied()
        auth_user = instance.auth_user
        auth_user.username = validated_data.get('phone_number', auth_user.username)
        auth_user.email = validated_data.get('email', auth_user.email)
        auth_user.first_name = validated_data.get('first_name', auth_user.first_name)
        auth_user.last_name = validated_data.get('last_name', auth_user.last_name)
        auth_user.save()

        instance.driver_license_image = validated_data.get('driver_license_image', instance.driver_license_image)
        instance.fhv_license_image = validated_data.get('fhv_license_image', instance.fhv_license_image)
        instance.address_proof_image = validated_data.get('address_proof_image', instance.address_proof_image)
        instance.defensive_cert_image = validated_data.get('defensive_cert_image', instance.defensive_cert_image)
        instance.save()

        return instance
