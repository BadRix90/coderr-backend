"""
API views for reviews_app.

This module contains review-related views.
"""

# Standard library
# (none needed)

# Third-party
from django.db.models import Avg
from rest_framework import filters, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

# Local
from users_app.models import UserProfile
from offers_app.models import Offer
from ..models import Review
from .serializers import ReviewSerializer


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
        """Get reviews with optional filters."""
        queryset = Review.objects.all()
        business_user_id = self.request.query_params.get('business_user_id')
        reviewer_id = self.request.query_params.get('reviewer_id')

        if business_user_id:
            queryset = queryset.filter(business_user_id=business_user_id)
        if reviewer_id:
            queryset = queryset.filter(reviewer_id=reviewer_id)

        return queryset

    def perform_create(self, serializer):
        """Create review - only customer allowed, one per business."""
        try:
            profile = UserProfile.objects.get(user=self.request.user)
        except UserProfile.DoesNotExist:
            raise PermissionDenied('UserProfile not found.')

        if profile.type != 'customer':
            raise PermissionDenied(
                "Only users with a customer profile may create reviews."
            )

        business_user = serializer.validated_data.get('business_user')
        if business_user is None:
            raise ValidationError({'business_user': 'This field is required.'})

        # Doc: one review per business per reviewer
        if Review.objects.filter(
            business_user=business_user, 
            reviewer=self.request.user
        ).exists():
            raise ValidationError({
                'detail': 'You have already reviewed this business user.'
            })

        serializer.save(reviewer=self.request.user)


@api_view(['GET'])
@permission_classes([AllowAny])
def base_info_view(request):
    """
    Get platform statistics.
    
    Endpoint: GET /api/base-info/
    """
    reviews = Review.objects.all()
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']

    return Response({
        'review_count': reviews.count(),
        'average_rating': round(avg_rating, 1) if avg_rating else 0.0,
        'business_profile_count': UserProfile.objects.filter(
            type='business'
        ).count(),
        'offer_count': Offer.objects.count(),
    })
