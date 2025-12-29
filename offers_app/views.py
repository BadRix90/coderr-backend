"""
API views for offers_app.

This module contains offer-related views.
"""

# Standard library
# (none needed)

# Third-party
from django.db.models import Min
from rest_framework import filters, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

# Local
from users_app.models import UserProfile
from ..models import Offer, OfferDetail
from .serializers import (
    OfferDetailSerializer,
    OfferListSerializer,
    OfferRetrieveSerializer,
    OfferWriteSerializer,
)


class OfferPagination(PageNumberPagination):
    """Pagination class for offers."""
    
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
    ordering_fields = ['updated_at', 'min_price']

    def get_queryset(self):
        """Get queryset with filters and annotations."""
        queryset = Offer.objects.all().annotate(
            min_price=Min('details__price'),
            min_delivery_time=Min('details__delivery_time_in_days'),
        ).order_by('-created_at')

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
            try:
                max_delivery_time = int(max_delivery_time)
                queryset = queryset.filter(
                    details__delivery_time_in_days__lte=max_delivery_time
                ).distinct()
            except (ValueError, TypeError):
                pass

        return queryset

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return OfferListSerializer
        if self.action == 'retrieve':
            return OfferRetrieveSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return OfferWriteSerializer
        return OfferListSerializer

    def get_permissions(self):
        """Return appropriate permissions based on action."""
        if self.action == 'list':
            return [AllowAny()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        """Create offer - only business users allowed."""
        try:
            profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            return Response(
                {'detail': 'UserProfile not found.'}, 
                status=status.HTTP_404_NOT_FOUND
            )

        if profile.type != 'business':
            return Response(
                {'detail': "Only users with type 'business' may create offers."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Update offer - only creator allowed."""
        instance = self.get_object()
        if instance.creator != request.user:
            return Response(
                {'detail': 'Forbidden'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete offer - only creator allowed."""
        instance = self.get_object()
        if instance.creator != request.user:
            return Response(
                {'detail': 'Forbidden'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)


class OfferDetailViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only ViewSet for OfferDetail."""

    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailSerializer
    permission_classes = [IsAuthenticated]