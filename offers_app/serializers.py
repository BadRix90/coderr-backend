"""
Serializers for offers_app.

This module contains all serializers for offer-related API endpoints.
"""

from rest_framework import serializers

from ..models import Offer, OfferDetail


class OfferDetailSerializer(serializers.ModelSerializer):
    """Serializer for OfferDetail model."""

    class Meta:
        model = OfferDetail
        fields = [
            'id', 'title', 'revisions', 'delivery_time_in_days',
            'price', 'features', 'offer_type'
        ]


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
        """Get details with URLs."""
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
        """Get minimum price from all details."""
        prices = list(obj.details.values_list('price', flat=True))
        return min(prices) if prices else None

    def get_min_delivery_time(self, obj):
        """Get minimum delivery time from all details."""
        times = list(obj.details.values_list('delivery_time_in_days', flat=True))
        return min(times) if times else None

    def get_user_details(self, obj):
        """Get creator user details."""
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
        """Get details with URLs."""
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
        """Get minimum price from all details."""
        prices = list(obj.details.values_list('price', flat=True))
        return min(prices) if prices else None

    def get_min_delivery_time(self, obj):
        """Get minimum delivery time from all details."""
        times = list(obj.details.values_list('delivery_time_in_days', flat=True))
        return min(times) if times else None


class OfferWriteSerializer(serializers.ModelSerializer):
    """Serializer for POST /api/offers/ and PATCH /api/offers/{id}/"""

    details = OfferDetailSerializer(many=True)

    class Meta:
        model = Offer
        fields = ['id', 'title', 'image', 'description', 'details']

    def validate_details(self, value):
        """Validate offer details."""
        request = self.context.get('request')
        if request and request.method == 'POST':
            if len(value) != 3:
                raise serializers.ValidationError(
                    'An offer must have exactly 3 details.'
                )
            types = [d.get('offer_type') for d in value]
            if sorted(types) != ['basic', 'premium', 'standard']:
                raise serializers.ValidationError(
                    "Details must include offer_type: basic, standard, premium."
                )
        for d in value:
            if not d.get('offer_type'):
                raise serializers.ValidationError(
                    'Each detail must include offer_type.'
                )
        return value

    def create(self, validated_data):
        """Create offer with details."""
        details_data = validated_data.pop('details', [])
        request = self.context.get('request')
        creator = validated_data.pop('creator', None) or getattr(
            request, 'user', None
        )
        offer = Offer.objects.create(creator=creator, **validated_data)
        for detail_data in details_data:
            OfferDetail.objects.create(offer=offer, **detail_data)
        return offer

    def update(self, instance, validated_data):
        """Update offer and details."""
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
                    defaults={
                        'title': '',
                        'revisions': 0,
                        'delivery_time_in_days': 1,
                        'price': 0,
                        'features': []
                    },
                )
                for field in [
                    'title', 'revisions', 'delivery_time_in_days',
                    'price', 'features'
                ]:
                    if field in d:
                        setattr(detail_obj, field, d[field])
                detail_obj.save()
        return instance