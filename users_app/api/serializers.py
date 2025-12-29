"""
Serializers for users_app.

This module contains all serializers for user-related API endpoints.
"""

from django.contrib.auth.models import User
from rest_framework import serializers

from ..models import UserProfile


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

    FIELDS_TO_FORCE_STRING = [
        'first_name', 'last_name', 'location', 'tel', 
        'description', 'working_hours'
    ]

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
    first_name = serializers.CharField(
        source='user.first_name', 
        required=False, 
        allow_blank=True
    )
    last_name = serializers.CharField(
        source='user.last_name', 
        required=False, 
        allow_blank=True
    )

    class Meta:
        model = UserProfile
        fields = [
            'user', 'username', 'first_name', 'last_name', 'file',
            'location', 'tel', 'description', 'working_hours',
            'type', 'email', 'created_at'
        ]
        read_only_fields = ['user', 'username', 'created_at']

    def update(self, instance, validated_data):
        """Update UserProfile and related User fields."""
        user_data = validated_data.pop('user', {})
        
        user = instance.user
        if 'email' in user_data:
            user.email = user_data['email']
        if 'first_name' in user_data:
            user.first_name = user_data['first_name']
        if 'last_name' in user_data:
            user.last_name = user_data['last_name']
        user.save()
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        return instance


class BusinessProfileListSerializer(_ProfileStringDefaultsMixin, serializers.ModelSerializer):
    """Serializer for GET /api/profiles/business/ (array response)."""

    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(
        source='user.first_name', 
        required=False, 
        allow_blank=True
    )
    last_name = serializers.CharField(
        source='user.last_name', 
        required=False, 
        allow_blank=True
    )

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
    first_name = serializers.CharField(
        source='user.first_name', 
        required=False, 
        allow_blank=True
    )
    last_name = serializers.CharField(
        source='user.last_name', 
        required=False, 
        allow_blank=True
    )

    class Meta:
        model = UserProfile
        fields = ['user', 'username', 'first_name', 'last_name', 'file', 'type']
        read_only_fields = fields


class RegistrationSerializer(serializers.Serializer):
    """Serializer for user registration."""

    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    repeated_password = serializers.CharField(write_only=True)
    type = serializers.ChoiceField(choices=['customer', 'business'])

    def validate_username(self, value):
        """Check if username already exists."""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                'A user with that username already exists.'
            )
        return value

    def validate(self, attrs):
        """Validate password match."""
        if attrs.get('password') != attrs.get('repeated_password'):
            raise serializers.ValidationError(
                {'repeated_password': 'Passwords do not match.'}
            )
        return attrs

    def create(self, validated_data):
        """Create new user with profile."""
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