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
    first_name = serializers.CharField(source='user.first_name')  # ← read_only ENTFERNEN
    last_name = serializers.CharField(source='user.last_name')    # ← read_only ENTFERNEN
    
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'username', 'email', 'first_name', 'last_name', 
                  'type', 'file', 'location', 'tel', 'description', 'working_hours', 
                  'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at', 'updated_at']
    
    def update(self, instance, validated_data):  # ← NEU: update() Methode

        user_data = {}
        if 'user' in validated_data:
            user_data = validated_data.pop('user')

        if user_data:
            user = instance.user
            user.first_name = user_data.get('first_name', user.first_name)
            user.last_name = user_data.get('last_name', user.last_name)
            user.save()
        
        return super().update(instance, validated_data)


class OfferDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfferDetail
        fields = ['id', 'title', 'revisions', 'delivery_time_in_days', 
                  'price', 'features', 'offer_type']


class OfferSerializer(serializers.ModelSerializer):
    details = OfferDetailSerializer(many=True)
    creator_name = serializers.CharField(source='creator.username', read_only=True)
    user = serializers.IntegerField(source='creator.id', read_only=True)
    creator_details = serializers.SerializerMethodField()
    
    min_delivery_time = serializers.SerializerMethodField()
    min_price = serializers.SerializerMethodField()
    
    class Meta:
        model = Offer
        fields = ['id', 'creator', 'creator_name', 'user', 'creator_details',
                  'title', 'image', 'description', 'details', 
                  'min_delivery_time', 'min_price',
                  'created_at', 'updated_at']
        read_only_fields = ['creator', 'created_at', 'updated_at']
    
    def get_creator_details(self, obj):
        profile = obj.creator.profile
        return {
            'first_name': obj.creator.first_name,
            'last_name': obj.creator.last_name,
            'username': obj.creator.username,
            'type': profile.type,
            'location': profile.location
        }
    
    def get_min_delivery_time(self, obj):
        if obj.details.exists():
            return min(d.delivery_time_in_days for d in obj.details.all())
        return None
    
    def get_min_price(self, obj):
        if obj.details.exists():
            return min(d.price for d in obj.details.all())
        return None
    
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
    offer_detail_id = serializers.PrimaryKeyRelatedField(
        queryset=OfferDetail.objects.all(),
        source='offer_detail',
        write_only=True
    )
    
    # Flatten: Alle Felder direkt auf Order-Ebene
    business_user = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    delivery_time_in_days = serializers.SerializerMethodField()
    revisions = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    features = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = ['id', 'buyer', 'offer_detail_id', 'business_user', 'title', 
                  'delivery_time_in_days', 'revisions', 'price', 'features',
                  'status', 'created_at', 'updated_at']
        read_only_fields = ['buyer', 'created_at', 'updated_at']
    
    def get_business_user(self, obj):
        return obj.offer_detail.offer.creator.id
    
    def get_title(self, obj):
        return obj.offer_detail.offer.title
    
    def get_delivery_time_in_days(self, obj):
        return obj.offer_detail.delivery_time_in_days
    
    def get_revisions(self, obj):
        return obj.offer_detail.revisions
    
    def get_price(self, obj):
        return str(obj.offer_detail.price)
    
    def get_features(self, obj):
        return obj.offer_detail.features


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