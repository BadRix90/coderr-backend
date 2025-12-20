from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Offer, OfferDetail, Order, Review


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'username', 'email', 'first_name', 'last_name', 
                  'type', 'file', 'location', 'description', 'working_hours', 
                  'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at', 'updated_at']


class OfferDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfferDetail
        fields = ['id', 'title', 'revisions', 'delivery_time_in_days', 
                  'price', 'features', 'offer_type']


class OfferSerializer(serializers.ModelSerializer):
    details = OfferDetailSerializer(many=True)
    creator_name = serializers.CharField(source='creator.username', read_only=True)
    
    class Meta:
        model = Offer
        fields = ['id', 'creator', 'creator_name', 'title', 'image', 
                  'description', 'details', 'created_at', 'updated_at']
        read_only_fields = ['creator', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        details_data = validated_data.pop('details')
        offer = Offer.objects.create(**validated_data)
        for detail_data in details_data:
            OfferDetail.objects.create(offer=offer, **detail_data)
        return offer
    
    def update(self, instance, validated_data):
        details_data = validated_data.pop('details', None)
        
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.save()
        
        if details_data:
            instance.details.all().delete()
            for detail_data in details_data:
                OfferDetail.objects.create(offer=instance, **detail_data)
        
        return instance


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'buyer', 'offer_detail', 'status', 'created_at', 'updated_at']
        read_only_fields = ['buyer', 'created_at', 'updated_at']


class ReviewSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.CharField(source='reviewer.username', read_only=True)
    business_user_name = serializers.CharField(source='business_user.username', read_only=True)
    
    class Meta:
        model = Review
        fields = ['id', 'reviewer', 'reviewer_name', 'business_user', 
                  'business_user_name', 'rating', 'description', 
                  'created_at', 'updated_at']
        read_only_fields = ['reviewer', 'created_at', 'updated_at']


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    type = serializers.ChoiceField(choices=['customer', 'business'])
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 'type']
    
    def create(self, validated_data):
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