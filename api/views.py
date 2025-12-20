from rest_framework import viewsets, status, filters
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Q, Count
from .models import UserProfile, Offer, OfferDetail, Order, Review
from .serializers import (
    UserProfileSerializer, OfferSerializer, OfferDetailSerializer,
    OrderSerializer, ReviewSerializer, RegistrationSerializer
)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    user = authenticate(username=username, password=password)
    if user:
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.id,
            'username': user.username
        })
    return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([AllowAny])
def registration_view(request):
    serializer = RegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token = Token.objects.create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.id,
            'username': user.username
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'], url_path='business')
    def business_profiles(self, request):
        profiles = UserProfile.objects.filter(type='business')
        serializer = self.get_serializer(profiles, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='customer')
    def customer_profiles(self, request):
        profiles = UserProfile.objects.filter(type='customer')
        serializer = self.get_serializer(profiles, many=True)
        return Response(serializer.data)


class OfferViewSet(viewsets.ModelViewSet):
    queryset = Offer.objects.all()
    serializer_class = OfferSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'title']
    
    def get_queryset(self):
        queryset = Offer.objects.all()
        creator_id = self.request.query_params.get('creator_id')
        max_delivery_time = self.request.query_params.get('max_delivery_time')
        
        if creator_id:
            queryset = queryset.filter(creator_id=creator_id)
        
        if max_delivery_time:
            queryset = queryset.filter(
                details__delivery_time_in_days__lte=max_delivery_time
            ).distinct()
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class OfferDetailViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailSerializer
    permission_classes = [IsAuthenticated]


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Order.objects.filter(buyer=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(buyer=self.request.user)


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'rating']
    
    def get_queryset(self):
        queryset = Review.objects.all()
        business_user_id = self.request.query_params.get('business_user_id')
        reviewer_id = self.request.query_params.get('reviewer_id')
        
        if business_user_id:
            queryset = queryset.filter(business_user_id=business_user_id)
        if reviewer_id:
            queryset = queryset.filter(reviewer_id=reviewer_id)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(reviewer=self.request.user)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_count_view(request, profile_id):
    count = Order.objects.filter(
        offer_detail__offer__creator_id=profile_id,
        status='in_progress'
    ).count()
    return Response({'order_count': count})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def completed_order_count_view(request, profile_id):
    count = Order.objects.filter(
        offer_detail__offer__creator_id=profile_id,
        status='completed'
    ).count()
    return Response({'order_count': count})


@api_view(['GET'])
@permission_classes([AllowAny])
def base_info_view(request):
    return Response({
        'business_count': UserProfile.objects.filter(type='business').count(),
        'customer_count': UserProfile.objects.filter(type='customer').count(),
        'offer_count': Offer.objects.count(),
    })