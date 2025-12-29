"""
API views for Coderr platform.

This module contains all viewsets and function-based views
for the REST API endpoints.
"""

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Min, Q
from rest_framework import filters, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

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
    """
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(username=username, password=password)
    if not user:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

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
    """GET/PATCH /api/profile/{pk}/ where pk is the USER id (per endpoint doc)."""

    serializer_class = ProfileDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        user_id = self.kwargs.get('pk')
        try:
            profile = UserProfile.objects.select_related('user').get(user_id=user_id)
        except UserProfile.DoesNotExist:
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
    """

    queryset = UserProfile.objects.all()
    serializer_class = ProfileDetailSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='business')
    def business_profiles(self, request):
        profiles = UserProfile.objects.filter(type='business')
        serializer = BusinessProfileListSerializer(profiles, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='customer')
    def customer_profile(self, request):
        profiles = UserProfile.objects.filter(type='customer')
        serializer = CustomerProfileListSerializer(profiles, many=True)
        return Response(serializer.data)


class OfferPagination(PageNumberPagination):
    page_size = 6
    page_size_query_param = 'page_size'
    max_page_size = 100

class OfferViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Offer CRUD operations.

    GET /api/offers/ is paginated (PageNumberPagination) per doc.
    """

    queryset = Offer.objects.all()
    pagination_class = OfferPagination
    serializer_class = OfferListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['updated_at', 'min_price']  # doc

    def get_queryset(self):
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
        if self.action == 'list':
            return OfferListSerializer
        if self.action == 'retrieve':
            return OfferRetrieveSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return OfferWriteSerializer
        return OfferListSerializer

    def get_permissions(self):
        if self.action == 'list':
            return [AllowAny()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        # Doc: only business can create offers
        try:
            profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            return Response({'detail': 'UserProfile not found.'}, status=status.HTTP_404_NOT_FOUND)

        if profile.type != 'business':
            return Response(
                {'detail': "Only users with type 'business' may create offers."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return super().create(request, *args, **kwargs)

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
    """

    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailSerializer
    permission_classes = [IsAuthenticated]


class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Order CRUD operations.

    Doc: GET /api/orders/ returns ARRAY (no pagination)
    Doc: POST /api/orders/ only customer
    Doc: PATCH /api/orders/{id}/ only business (offer creator)
    """

    queryset = Order.objects.all()
    pagination_class = None  # doc: array
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Order.objects.select_related(
            'buyer',
            'offer_detail__offer__creator'
        ).filter(
            Q(buyer=user) | Q(offer_detail__offer__creator=user)
        )

    def perform_create(self, serializer):
        # Doc: only customer can create orders
        try:
            profile = UserProfile.objects.get(user=self.request.user)
        except UserProfile.DoesNotExist:
            raise PermissionDenied('UserProfile not found.')

        if profile.type != 'customer':
            raise PermissionDenied("Only users with type 'customer' may create orders.")

        serializer.save(buyer=self.request.user)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        # Doc: only business (offer creator) can update order status
        if instance.offer_detail.offer.creator != request.user:
            return Response(
                {'detail': 'You do not have permission to update this order.'},
                status=status.HTTP_403_FORBIDDEN
            )

        return super().update(request, *args, **kwargs)


class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Review CRUD operations.

    Doc: GET /api/reviews/ returns ARRAY (no pagination)
    Doc: ordering only by 'updated_at' or 'rating'
    Doc: POST only customer + only one review per business_user per reviewer
    """

    queryset = Review.objects.all()
    pagination_class = None  # doc: array
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['updated_at', 'rating']  # doc

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
        # Doc: only customer can create reviews
        try:
            profile = UserProfile.objects.get(user=self.request.user)
        except UserProfile.DoesNotExist:
            raise PermissionDenied('UserProfile not found.')

        if profile.type != 'customer':
            raise PermissionDenied("Only users with a customer profile may create reviews.")

        business_user = serializer.validated_data.get('business_user')
        if business_user is None:
            raise ValidationError({'business_user': 'This field is required.'})

        # Doc: one review per business per reviewer
        if Review.objects.filter(business_user=business_user, reviewer=self.request.user).exists():
            # Doku nennt 400/403 je nach Text – wir nehmen 400 (Bad Request) wie beschrieben möglich
            raise ValidationError({'detail': 'You have already reviewed this business user.'})

        serializer.save(reviewer=self.request.user)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_count_view(request, business_user_id):
    if not User.objects.filter(id=business_user_id).exists():
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    count = Order.objects.filter(
        offer_detail__offer__creator_id=business_user_id,
        status='in_progress'
    ).count()
    return Response({'order_count': count})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def completed_order_count_view(request, business_user_id):
    if not User.objects.filter(id=business_user_id).exists():
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    count = Order.objects.filter(
        offer_detail__offer__creator_id=business_user_id,
        status='completed'
    ).count()
    return Response({'completed_order_count': count})


@api_view(['GET'])
@permission_classes([AllowAny])
def base_info_view(request):
    from django.db.models import Avg

    reviews = Review.objects.all()
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']

    return Response({
        'review_count': reviews.count(),
        'average_rating': round(avg_rating, 1) if avg_rating else 0.0,
        'business_profile_count': UserProfile.objects.filter(type='business').count(),
        'offer_count': Offer.objects.count(),
    })
