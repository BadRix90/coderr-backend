"""
Serializers for orders_app.

This module contains all serializers for order-related API endpoints.
"""

from rest_framework import serializers

from offers_app.models import OfferDetail
from ..models import Order


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
        """Get customer user ID."""
        return obj.buyer.id

    def get_business_user(self, obj):
        """Get business user ID."""
        return obj.offer_detail.offer.creator.id

    def get_title(self, obj):
        """Get title from OfferDetail (NOT from Offer!)."""
        return obj.offer_detail.title

    def get_delivery_time_in_days(self, obj):
        """Get delivery time from OfferDetail."""
        return obj.offer_detail.delivery_time_in_days

    def get_revisions(self, obj):
        """Get revisions from OfferDetail."""
        return obj.offer_detail.revisions

    def get_price(self, obj):
        """Get price from OfferDetail."""
        return obj.offer_detail.price

    def get_features(self, obj):
        """Get features from OfferDetail."""
        return obj.offer_detail.features

    def get_offer_type(self, obj):
        """Get offer type from OfferDetail."""
        return obj.offer_detail.offer_type
