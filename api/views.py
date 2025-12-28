"""
API views for Coderr platform.

This module contains all viewsets and function-based views
for the REST API endpoints.
"""

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.db.models import Min, Q
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.exceptions import PermissionDenied

from .models import Offer, OfferDetail, Order, Review, UserProfile
from .serializers import (
    OfferDetailSerializer,
    OfferListSerializer,
    OfferRetrieveSerializer,
    OfferWriteSerializer,
    OrderSerializer,
    RegistrationSerializer,
    ReviewSerializer,
    ProfileDetailSerializer,
    BusinessProfileListSerializer,
    CustomerProfileListSerializer,
)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Authenticate user and return auth token.

    Args:
        request: POST request with username and password

    Returns:
        Response: Token and user info or error message
    """
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(username=username, password=password)
    if not user:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

    token, _ = Token.objects.get_or_create(user=user)
    # Doku: exakt diese Felder
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

    Args:
        request: POST request with registration data

    Returns:
        Response: Token and user info or validation errors
    """
    serializer = RegistrationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = serializer.save()
    token = Token.objects.create(user=user)

    # Doku: exakt diese Felder
    return Response({
        'token': token.key,
        'username': user.username,
        'email': user.email,
        'user_id': user.id,
    }, status=status.HTTP_201_CREATED)


class ProfileDetailView(RetrieveUpdateAPIView):
    """GET/PATCH /api/profile/{pk}/ where pk is the USER id (per endpoint doc)."""

    serializer_class = ProfileDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        user_id = self.kwargs.get('pk')
        try:
            profile = UserProfile.objects.select_related('user').get(user_id=user_id)
        except UserProfile.DoesNotExist:
            # Doku: 404 wenn Profil nicht gefunden
            from rest_framework.exceptions import NotFound

            raise NotFound('UserProfile not found')

        return profile

    def patch(self, request, *args, **kwargs):
        # Doku: User darf NUR sein eigenes Profil bearbeiten
        if request.user.id != int(self.kwargs.get('pk')):
            raise PermissionDenied('You do not have permission to edit this profile.')
        return super().patch(request, *args, **kwargs)


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for UserProfile CRUD operations.

    Provides endpoints for viewing and editing user profiles,
    plus custom actions for filtering by user type.
    """

    queryset = UserProfile.objects.all()
    serializer_class = ProfileDetailSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='business')
    def business_profiles(self, request):
        """
        List all business user profiles.

        Returns:
            Response: List of business profiles
        """
        profiles = UserProfile.objects.filter(type='business')
        serializer = BusinessProfileListSerializer(profiles, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='customer')
    def customer_profile(self, request):
        """
        List all customer user profiles.

        Returns:
            Response: List of customer profiles
        """
        profiles = UserProfile.objects.filter(type='customer')
        serializer = CustomerProfileListSerializer(profiles, many=True)
        return Response(serializer.data)


class OfferViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Offer CRUD operations.

    Supports search, ordering, and filtering by creator and delivery time.
    """

    queryset = Offer.objects.all()
    pagination_class = PageNumberPagination
    # Serializer is selected dynamically per action to match Endpoint-Doku exactly.
    serializer_class = OfferListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    # Doku: ordering supports 'updated_at' or 'min_price'
    ordering_fields = ['updated_at', 'min_price']

    def get_queryset(self):
        """
        Get filtered queryset based on query parameters.

        Supports filtering by creator_id and max_delivery_time.

        Returns:
            QuerySet: Filtered Offer queryset
        """
        queryset = Offer.objects.all().annotate(
            min_price=Min('details__price'),
            min_delivery_time=Min('details__delivery_time_in_days'),
        )
        creator_id = self.request.query_params.get('creator_id')
        min_price = self.request.query_params.get('min_price')
        max_delivery_time = self.request.query_params.get('max_delivery_time')

        if creator_id:
            queryset = queryset.filter(creator_id=creator_id)

        if min_price:
            try:
                queryset = queryset.filter(details__price__gte=min_price)
            except Exception:
                pass

        if max_delivery_time:
            queryset = queryset.filter(
                details__delivery_time_in_days__lte=max_delivery_time
            ).distinct()

        return queryset

    def get_serializer_class(self):
        """Return serializer per action (exact response shapes per doc)."""
        if self.action == 'list':
            return OfferListSerializer
        if self.action == 'retrieve':
            return OfferRetrieveSerializer
        # POST and PATCH must return the full details objects per doc
        if self.action in ['create', 'update', 'partial_update']:
            return OfferWriteSerializer
        return OfferListSerializer

    def get_permissions(self):
        """Match endpoint documentation exactly for auth requirements."""
        if self.action == 'list':
            return [AllowAny()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        """
        Save offer with current user as creator.

        Args:
            serializer: Validated OfferSerializer instance
        """
        # Doku: nur Business-User dürfen Offers erstellen
        try:
            if self.request.user.profile.type != 'business':
                return Response(
                    {'detail': "Only users with type 'business' may create offers."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        except UserProfile.DoesNotExist:
            return Response({'detail': 'UserProfile not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer.save(creator=self.request.user)

    def create(self, request, *args, **kwargs):
        # perform_create may return a Response (permission error)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        maybe_response = self.perform_create(serializer)
        if isinstance(maybe_response, Response):
            return maybe_response
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.creator != request.user:
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.creator != request.user:
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)


class OfferDetailViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for OfferDetail.

    Provides endpoints for viewing individual offer pricing tiers.
    """

    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailSerializer
    permission_classes = [IsAuthenticated]


class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Order CRUD operations.

    Users can only view and manage their own orders.
    Pagination is disabled for complete order history.
    """

    queryset = Order.objects.all()
    pagination_class = PageNumberPagination
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Get orders for current user only.

        Returns:
            QuerySet: User's orders (both as customer and business)
        """
        user = self.request.user
        return Order.objects.filter(
            Q(buyer=user) |
            Q(offer_detail__offer__creator=user)
        )

    def perform_create(self, serializer):
        """
        Save order with current user as buyer.

        Args:
            serializer: Validated OrderSerializer instance
        """
        serializer.save(buyer=self.request.user)

    def update(self, request, *args, **kwargs):
        """
        Update order status (only business users can update their orders).

        Returns:
            Response: Updated order or error
        """
        instance = self.get_object()

        # Only business user (offer creator) can update order status
        if instance.offer_detail.offer.creator != request.user:
            return Response(
                {'detail': 'You do not have permission to update this order.'},
                status=status.HTTP_403_FORBIDDEN
            )

        return super().update(request, *args, **kwargs)


class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Review CRUD operations.

    Supports filtering by business_user_id and reviewer_id.
    Pagination enabled for API consistency.
    """

    queryset = Review.objects.all()
    pagination_class = PageNumberPagination
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'rating']

    def get_queryset(self):
        """
        Get filtered queryset based on query parameters.

        Supports filtering by business_user_id and reviewer_id.

        Returns:
            QuerySet: Filtered Review queryset
        """
        queryset = Review.objects.all()
        business_user_id = self.request.query_params.get('business_user_id')
        reviewer_id = self.request.query_params.get('reviewer_id')

        if business_user_id:
            queryset = queryset.filter(business_user_id=business_user_id)
        if reviewer_id:
            queryset = queryset.filter(reviewer_id=reviewer_id)

        return queryset

    def perform_create(self, serializer):
        """
        Save review with current user as reviewer.

        Args:
            serializer: Validated ReviewSerializer instance
        """
        serializer.save(reviewer=self.request.user)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_count_view(request, business_user_id):
    """
    Get count of in-progress orders for a business user.

    Args:
        request: GET request
        profile_id: ID of business user profile

    Returns:
        Response: Order count or 404 if profile not found
    """
    if not User.objects.filter(id=business_user_id).exists():
        return Response(
            {'error': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    count = Order.objects.filter(
        offer_detail__offer__creator_id=business_user_id,
        status='in_progress'
    ).count()
    return Response({'order_count': count})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def completed_order_count_view(request, business_user_id):
    """
    Get count of completed orders for a business user.

    Args:
        request: GET request
        profile_id: ID of business user profile

    Returns:
        Response: Order count or 404 if profile not found
    """
    if not User.objects.filter(id=business_user_id).exists():
        return Response(
            {'error': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    count = Order.objects.filter(
        offer_detail__offer__creator_id=business_user_id,
        status='completed'
    ).count()
    # Doku: exakt dieser Key
    return Response({'completed_order_count': count})


@api_view(['GET'])
@permission_classes([AllowAny])
def base_info_view(request):
    """
    Get platform statistics.

    Returns review count, average rating, business profile count and offer count
    per API documentation.

    Args:
        request: GET request

    Returns:
        Response: Platform statistics
    """
    from django.db.models import Avg

    reviews = Review.objects.all()
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']

    return Response({
        'review_count': reviews.count(),
        'average_rating': round(avg_rating, 1) if avg_rating else 0.0,
        'business_profile_count': UserProfile.objects.filter(type='business').count(),
        'offer_count': Offer.objects.count(),
    })