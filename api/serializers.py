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


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for UserProfile model with nested User fields.
    
    Allows updating first_name and last_name on the related User model.
    Provides flattened access to User fields for easier frontend consumption.
    """
    
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email')
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'username', 'email', 'first_name', 'last_name', 
            'type', 'file', 'location', 'tel', 'description', 'working_hours', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']
    
    def update(self, instance, validated_data):
        """
        Update UserProfile and related User fields.
        
        Args:
            instance (UserProfile): UserProfile instance to update
            validated_data (dict): Validated data from request
            
        Returns:
            UserProfile: Updated UserProfile instance
        """
        user_data = {}
        if 'user' in validated_data:
            user_data = validated_data.pop('user')

        if user_data:
            user = instance.user
            user.first_name = user_data.get('first_name', user.first_name)
            user.last_name = user_data.get('last_name', user.last_name)
            user.email = user_data.get('email', user.email)
            user.save()
        
        return super().update(instance, validated_data)


class OfferDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for OfferDetail model.
    
    Represents a single pricing tier of an offer.
    """
    
    class Meta:
        model = OfferDetail
        fields = [
            'id', 'title', 'revisions', 'delivery_time_in_days', 
            'price', 'features', 'offer_type'
        ]


class OfferSerializer(serializers.ModelSerializer):
    """
    Serializer for Offer model with nested OfferDetails.
    
    Includes creator information and computed minimum values
    across all pricing tiers.
    """
    
    details = OfferDetailSerializer(many=True)
    creator_name = serializers.CharField(
        source='creator.username', 
        read_only=True
    )
    user = serializers.IntegerField(source='creator.id', read_only=True)
    creator_details = serializers.SerializerMethodField()
    min_delivery_time = serializers.SerializerMethodField()
    min_price = serializers.SerializerMethodField()
    
    class Meta:
        model = Offer
        fields = [
            'id', 'creator', 'creator_name', 'user', 'creator_details',
            'title', 'image', 'description', 'details', 
            'min_delivery_time', 'min_price',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['creator', 'created_at', 'updated_at']
    
    def get_creator_details(self, obj):
        """
        Get detailed creator information.
        
        Args:
            obj (Offer): Offer instance
            
        Returns:
            dict: Creator profile details
        """
        profile = obj.creator.profile
        return {
            'first_name': obj.creator.first_name,
            'last_name': obj.creator.last_name,
            'username': obj.creator.username,
            'type': profile.type,
            'location': profile.location
        }
    
    def get_min_delivery_time(self, obj):
        """
        Calculate minimum delivery time across all tiers.
        
        Args:
            obj (Offer): Offer instance
            
        Returns:
            int or None: Minimum delivery time in days
        """
        if obj.details.exists():
            return min(d.delivery_time_in_days for d in obj.details.all())
        return None
    
    def get_min_price(self, obj):
        """
        Calculate minimum price across all tiers.
        
        Args:
            obj (Offer): Offer instance
            
        Returns:
            Decimal or None: Minimum price
        """
        if obj.details.exists():
            return min(d.price for d in obj.details.all())
        return None
    
    def create(self, validated_data):
        """
        Create Offer with nested OfferDetails.
        
        Args:
            validated_data (dict): Validated data from request
            
        Returns:
            Offer: Created Offer instance with details
        """
        details_data = validated_data.pop('details')
        offer = Offer.objects.create(**validated_data)
        for detail_data in details_data:
            OfferDetail.objects.create(offer=offer, **detail_data)
        return offer
    
    def update(self, instance, validated_data):
        """
        Update Offer and replace all OfferDetails.
        
        Args:
            instance (Offer): Offer instance to update
            validated_data (dict): Validated data from request
            
        Returns:
            Offer: Updated Offer instance
        """
        details_data = validated_data.pop('details', None)
        
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get(
            'description', 
            instance.description
        )
        instance.save()
        
        if details_data:
            instance.details.all().delete()
            for detail_data in details_data:
                OfferDetail.objects.create(offer=instance, **detail_data)
        
        return instance


class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for Order model with flattened offer details.
    
    Flattens nested offer_detail and offer data to top level
    for easier frontend consumption.
    """
    
    offer_detail_id = serializers.PrimaryKeyRelatedField(
        queryset=OfferDetail.objects.all(),
        source='offer_detail',
        write_only=True
    )
    
    business_user = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    delivery_time_in_days = serializers.SerializerMethodField()
    revisions = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    features = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'buyer', 'offer_detail_id', 'business_user', 'title', 
            'delivery_time_in_days', 'revisions', 'price', 'features',
            'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['buyer', 'created_at', 'updated_at']
    
    def get_business_user(self, obj):
        """Get ID of business user who created the offer."""
        return obj.offer_detail.offer.creator.id
    
    def get_title(self, obj):
        """Get title of the purchased offer."""
        return obj.offer_detail.offer.title
    
    def get_delivery_time_in_days(self, obj):
        """Get delivery time from offer detail."""
        return obj.offer_detail.delivery_time_in_days
    
    def get_revisions(self, obj):
        """Get number of revisions from offer detail."""
        return obj.offer_detail.revisions
    
    def get_price(self, obj):
        """Get price from offer detail as string."""
        return str(obj.offer_detail.price)
    
    def get_features(self, obj):
        """Get features list from offer detail."""
        return obj.offer_detail.features


class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for Review model.
    
    Includes reviewer and business user names for display.
    """
    
    reviewer_name = serializers.CharField(
        source='reviewer.username', 
        read_only=True
    )
    business_user_name = serializers.CharField(
        source='business_user.username', 
        read_only=True
    )
    
    class Meta:
        model = Review
        fields = [
            'id', 'reviewer', 'reviewer_name', 'business_user', 
            'business_user_name', 'rating', 'description', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['reviewer', 'created_at', 'updated_at']


class RegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    
    Creates both a Django User and associated UserProfile.
    """
    
    password = serializers.CharField(write_only=True)
    type = serializers.ChoiceField(choices=['customer', 'business'])
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 
            'first_name', 'last_name', 'type'
        ]
    
    def create(self, validated_data):
        """
        Create User and UserProfile.
        
        Args:
            validated_data (dict): Validated registration data
            
        Returns:
            User: Created User instance
        """
        user_type = validated_data.pop('type')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        UserProfile.objects.create(user=user, type=user_type)
        return user