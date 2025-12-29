"""
API views for orders_app.

This module contains order-related views.
"""

# Standard library
# (none needed)

# Third-party
from django.contrib.auth.models import User
from django.db.models import Avg, Q
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

# Local
from users_app.models import UserProfile
from ..models import Order
from .serializers import OrderSerializer


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
        """Get orders for current user (as buyer or business)."""
        user = self.request.user
        return Order.objects.select_related(
            'buyer',
            'offer_detail__offer__creator'
        ).filter(
            Q(buyer=user) | Q(offer_detail__offer__creator=user)
        )

    def perform_create(self, serializer):
        """Create order - only customer allowed."""
        try:
            profile = UserProfile.objects.get(user=self.request.user)
        except UserProfile.DoesNotExist:
            raise PermissionDenied('UserProfile not found.')

        if profile.type != 'customer':
            raise PermissionDenied(
                "Only users with type 'customer' may create orders."
            )

        serializer.save(buyer=self.request.user)

    def update(self, request, *args, **kwargs):
        """Update order - only business (offer creator) allowed."""
        instance = self.get_object()

        # Doc: only business (offer creator) can update order status
        if instance.offer_detail.offer.creator != request.user:
            return Response(
                {'detail': 'You do not have permission to update this order.'},
                status=status.HTTP_403_FORBIDDEN
            )

        return super().update(request, *args, **kwargs)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_count_view(request, business_user_id):
    """
    Get count of in-progress orders for a business user.
    
    Endpoint: GET /api/order-count/{business_user_id}/
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
    
    Endpoint: GET /api/completed-order-count/{business_user_id}/
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
    return Response({'completed_order_count': count})
