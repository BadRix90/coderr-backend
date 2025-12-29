"""
API views for users_app.

This module contains authentication and profile-related views.
"""

# Standard library
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

# Third-party
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

# Local
from ..models import UserProfile
from .serializers import (
    BusinessProfileListSerializer,
    CustomerProfileListSerializer,
    ProfileDetailSerializer,
    RegistrationSerializer,
)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Authenticate user and return auth token.
    
    Endpoint: POST /api/login/
    """
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(username=username, password=password)
    if not user:
        return Response(
            {'error': 'Invalid credentials'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

    token, _ = Token.objects.get_or_create(user=user)
    return Response({
        'token': token.key,
        'username': user.username,
        'email': user.email,
        'user_id': user.id,
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def registration_view(request):
    """
    Register new user with profile.
    
    Endpoint: POST /api/registration/
    """
    serializer = RegistrationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = serializer.save()
    token = Token.objects.create(user=user)

    return Response({
        'token': token.key,
        'username': user.username,
        'email': user.email,
        'user_id': user.id,
    }, status=status.HTTP_201_CREATED)


class ProfileDetailView(RetrieveUpdateAPIView):
    """
    GET/PATCH /api/profile/{pk}/ where pk is the USER id.
    """

    serializer_class = ProfileDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """Get UserProfile by user_id."""
        user_id = self.kwargs.get('pk')
        try:
            profile = UserProfile.objects.select_related('user').get(
                user_id=user_id
            )
        except UserProfile.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound('UserProfile not found')
        return profile

    def patch(self, request, *args, **kwargs):
        """Update profile - only owner can edit."""
        if request.user.id != int(self.kwargs.get('pk')):
            raise PermissionDenied(
                'You do not have permission to edit this profile.'
            )
        return super().patch(request, *args, **kwargs)


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for UserProfile CRUD operations.
    
    Endpoints:
    - GET /api/profiles/business/ - List all business profiles
    - GET /api/profiles/customer/ - List all customer profiles
    """

    queryset = UserProfile.objects.all()
    serializer_class = ProfileDetailSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='business')
    def business_profiles(self, request):
        """List all business profiles."""
        profiles = UserProfile.objects.filter(type='business')
        serializer = BusinessProfileListSerializer(profiles, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='customer')
    def customer_profile(self, request):
        """List all customer profiles."""
        profiles = UserProfile.objects.filter(type='customer')
        serializer = CustomerProfileListSerializer(profiles, many=True)
        return Response(serializer.data)