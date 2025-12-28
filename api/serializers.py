"""
DRF serializers for Coderr API.

This module contains all serializers for the REST API, handling
data validation, transformation, and nested object creation.
"""

from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Offer, OfferDetail, Order, Review, UserProfile


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for Django User model.

    Exposes basic user information for API responses.
    """

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class _ProfileStringDefaultsMixin:
    """Ensure specific fields are never null in responses (must be '' per doc)."""

    FIELDS_TO_FORCE_STRING = ['first_name', 'last_name', 'location', 'tel', 'description', 'working_hours']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        for field in self.FIELDS_TO_FORCE_STRING:
            if data.get(field) is None:
                data[field] = ''
        return data


class ProfileDetailSerializer(_ProfileStringDefaultsMixin, serializers.ModelSerializer):
    """Serializer for GET/PATCH /api/profile/{pk}/ (pk=user id)."""

    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', required=False)
    first_name = serializers.CharField(source='user.first_name', required=False, allow_blank=True)
    last_name = serializers.CharField(source='user.last_name', required=False, allow_blank=True)

    class Meta:
        model = UserProfile
        fields = [
            'user', 'username', 'first_name', 'last_name', 'file',
            'location', 'tel', 'description', 'working_hours',
            'type', 'email', 'created_at'
        ]
        read_only_fields = ['user', 'username', 'created_at']

    def update(self, instance, validated_data):
        """
        Update UserProfile and related User fields.
        """
        # FIX: email kommt als Top-Level field (source='user.email'), nicht im user dict
        email = validated_data.pop('email', None)

        user_data = validated_data.pop('user', {})

        user = instance.user
        if user_data:
            user.first_name = user_data.get('first_name', user.first_name)
            user.last_name = user_data.get('last_name', user.last_name)

        if email is not None:
            user.email = email

        user.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance


class BusinessProfileListSerializer(_ProfileStringDefaultsMixin, serializers.ModelSerializer):
    """Serializer for GET /api/profiles/business/ (array response)."""

    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(source='user.first_name', required=False, allow_blank=True)
    last_name = serializers.CharField(source='user.last_name', required=False, allow_blank=True)

    class Meta:
        model = UserProfile
        fields = [
            'user', 'username', 'first_name', 'last_name', 'file',
            'location', 'tel', 'description', 'working_hours', 'type'
        ]
        read_only_fields = fields


class CustomerProfileListSerializer(_ProfileStringDefaultsMixin, serializers.ModelSerializer):
    """Serializer for GET /api/profiles/customer/ (array response)."""

    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(source='user.first_name', required=False, allow_blank=True)
    last_name = serializers.CharField(source='user.last_name', required=False, allow_blank=True)

    class Meta:
        model = UserProfile
        fields = ['user', 'username', 'first_name', 'last_name', 'file', 'type']
        read_only_fields = fields


class OfferDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for OfferDetail model.
    """

    class Meta:
        model = OfferDetail
        fields = [
            'id', 'title', 'revisions', 'delivery_time_in_days',
            'price', 'features', 'offer_type'
        ]


class OfferListDetailLinkSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    url = serializers.CharField()


class OfferListSerializer(serializers.ModelSerializer):
    """Serializer for GET /api/offers/ (paginated, exact shape per doc)."""

    user = serializers.IntegerField(source='creator.id', read_only=True)
    details = serializers.SerializerMethodField()
    min_price = serializers.SerializerMethodField()
    min_delivery_time = serializers.SerializerMethodField()
    user_details = serializers.SerializerMethodField()

    class Meta:
        model = Offer
        fields = [
            'id', 'user', 'title', 'image', 'description',
            'created_at', 'updated_at',
            'details',
            'min_price', 'min_delivery_time',
            'user_details',
        ]

    def get_details(self, obj):
        request = self.context.get('request')
        items = []
        for d in obj.details.all().order_by('id'):
            url = f"/api/offerdetails/{d.id}/"
            if request is not None:
                try:
                    url = request.build_absolute_uri(url)
                except Exception:
                    pass
            items.append({'id': d.id, 'url': url})
        return items

    def get_min_price(self, obj):
        prices = list(obj.details.values_list('price', flat=True))
        return min(prices) if prices else None

    def get_min_delivery_time(self, obj):
        times = list(obj.details.values_list('delivery_time_in_days', flat=True))
        return min(times) if times else None

    def get_user_details(self, obj):
        return {
            'first_name': obj.creator.first_name or '',
            'last_name': obj.creator.last_name or '',
            'username': obj.creator.username,
        }


class OfferRetrieveSerializer(serializers.ModelSerializer):
    """Serializer for GET /api/offers/{id}/ (exact shape per doc)."""

    user = serializers.IntegerField(source='creator.id', read_only=True)
    details = serializers.SerializerMethodField()
    min_price = serializers.SerializerMethodField()
    min_delivery_time = serializers.SerializerMethodField()

    class Meta:
        model = Offer
        fields = [
            'id', 'user', 'title', 'image', 'description',
            'created_at', 'updated_at',
            'details',
            'min_price', 'min_delivery_time',
        ]

    def get_details(self, obj):
        request = self.context.get('request')
        items = []
        for d in obj.details.all().order_by('id'):
            url = f"/api/offerdetails/{d.id}/"
            if request is not None:
                try:
                    url = request.build_absolute_uri(url)
                except Exception:
                    pass
            items.append({'id': d.id, 'url': url})
        return items

    def get_min_price(self, obj):
        prices = list(obj.details.values_list('price', flat=True))
        return min(prices) if prices else None

    def get_min_delivery_time(self, obj):
        times = list(obj.details.values_list('delivery_time_in_days', flat=True))
        return min(times) if times else None


class OfferWriteSerializer(serializers.ModelSerializer):
    """Serializer for POST /api/offers/ and PATCH /api/offers/{id}/"""

    details = OfferDetailSerializer(many=True)

    class Meta:
        model = Offer
        fields = ['id', 'title', 'image', 'description', 'details']

    def validate_details(self, value):
        request = self.context.get('request')
        if request and request.method == 'POST':
            if len(value) != 3:
                raise serializers.ValidationError('An offer must have exactly 3 details.')
            types = [d.get('offer_type') for d in value]
            if sorted(types) != ['basic', 'premium', 'standard']:
                raise serializers.ValidationError("Details must include offer_type: basic, standard, premium.")
        for d in value:
            if not d.get('offer_type'):
                raise serializers.ValidationError('Each detail must include offer_type.')
        return value

    def create(self, validated_data):
        details_data = validated_data.pop('details', [])
        request = self.context.get('request')
        creator = validated_data.pop('creator', None) or getattr(request, 'user', None)
        offer = Offer.objects.create(creator=creator, **validated_data)
        for detail_data in details_data:
            OfferDetail.objects.create(offer=offer, **detail_data)
        return offer

    def update(self, instance, validated_data):
        details_data = validated_data.pop('details', None)

        for attr in ['title', 'description', 'image']:
            if attr in validated_data:
                setattr(instance, attr, validated_data[attr])
        instance.save()

        if details_data is not None:
            for d in details_data:
                offer_type = d.get('offer_type')
                detail_obj, _created = OfferDetail.objects.get_or_create(
                    offer=instance,
                    offer_type=offer_type,
                    defaults={'title': '', 'revisions': 0, 'delivery_time_in_days': 1, 'price': 0, 'features': []},
                )
                for field in ['title', 'revisions', 'delivery_time_in_days', 'price', 'features']:
                    if field in d:
                        setattr(detail_obj, field, d[field])
                detail_obj.save()
        return instance


class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for Order model with flattened offer details.
    """

    offer_detail_id = serializers.PrimaryKeyRelatedField(
        queryset=OfferDetail.objects.all(),
        source='offer_detail',
        write_only=True
    )

    customer_user = serializers.SerializerMethodField()
    business_user = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    delivery_time_in_days = serializers.SerializerMethodField()
    revisions = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    features = serializers.SerializerMethodField()
    offer_type = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'customer_user', 'business_user', 'title',
            'revisions', 'delivery_time_in_days', 'price', 'features',
            'offer_type', 'status', 'created_at', 'updated_at', 'offer_detail_id'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_customer_user(self, obj):
        return obj.buyer.id

    def get_business_user(self, obj):
        return obj.offer_detail.offer.creator.id

    def get_title(self, obj):
        return obj.offer_detail.offer.title

    def get_delivery_time_in_days(self, obj):
        return obj.offer_detail.delivery_time_in_days

    def get_revisions(self, obj):
        return obj.offer_detail.revisions

    def get_price(self, obj):
        return obj.offer_detail.price

    def get_features(self, obj):
        return obj.offer_detail.features

    def get_offer_type(self, obj):
        return obj.offer_detail.offer_type


class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for Review model (doc fields only).
    """

    class Meta:
        model = Review
        fields = ['id', 'business_user', 'reviewer', 'rating', 'description', 'created_at', 'updated_at']
        read_only_fields = ['reviewer', 'created_at', 'updated_at']


class RegistrationSerializer(serializers.Serializer):
    """
    Serializer for user registration.
    """

    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    repeated_password = serializers.CharField(write_only=True)
    type = serializers.ChoiceField(choices=['customer', 'business'])

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('repeated_password'):
            raise serializers.ValidationError({'repeated_password': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        user_type = validated_data.pop('type')
        validated_data.pop('repeated_password', None)

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            first_name='',
            last_name=''
        )
        UserProfile.objects.create(user=user, type=user_type)
        return user
