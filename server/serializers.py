# -*- encoding:utf-8 -*-
from __future__ import unicode_literals

from rest_framework import serializers

from models import Car, UserAccount, Booking


class CarSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    listing_features = serializers.SerializerMethodField()
    cost = serializers.SerializerMethodField()
    cost_time = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Car
        fields = (
            'id',
            'name',
            'listing_features',
            'cost',
            'cost_time',
            'image_url',
        )

    def get_name(self, obj):
        return unicode(obj.make_model)

    def get_listing_features(self, obj):
        return '{} minimum lease ∙ {}, {}, ∙ Idlecars Certified'.format(
            Car.MIN_LEASE_CHOICES[obj.min_lease],
            obj.owner.city,
            obj.owner.state_code,
        )

    def get_cost(self, obj):
        return unicode(obj.solo_cost)

    def get_cost_time(self, obj):
        return 'a week'

    def get_image_url(self, obj):
        if obj.make_model and obj.make_model.image_filename:
            return 'https://s3.amazonaws.com/images.idlecars.com/{}'.format(obj.make_model.image_filename)
        else:
            return 'https://s3.amazonaws.com/images.idlecars.com/toyota_avalon.jpg' # TODO - slugbug


class UserAccountSerializer(serializers.ModelSerializer):
    email = serializers.CharField(required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)

    class Meta:
        model = UserAccount

    def create(self, validated_data):
        return UserAccount.objects.create(**validated_data)
 

class BookingSerializer(serializers.ModelSerializer):
    car_id = serializers.PrimaryKeyRelatedField(queryset=Car.objects.all())
    user_account = UserAccountSerializer(read_only=False)

    class Meta:
        model = Booking
        fields = ('user_account', 'car_id')

    def is_valid(self, raise_exception=False):
        # TODO - check that the car is available to be booked
        super(BookingSerializer, self).is_valid(raise_exception=True)

    def create(self, validated_data):
        user_account_data = validated_data.pop('user_account')
        user_account = UserAccount.objects.create(**user_account_data)
        car = validated_data['car_id']
        booking = Booking.objects.create(
            user_account = user_account,
            car = car,
        )
        return booking
