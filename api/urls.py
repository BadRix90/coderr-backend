from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    login_view, registration_view, ProfileDetailView, UserProfileViewSet, OfferViewSet,
    OfferDetailViewSet, OrderViewSet, ReviewViewSet,
    order_count_view, completed_order_count_view, base_info_view
)

router = DefaultRouter()
router.register(r'offers', OfferViewSet, basename='offer')
router.register(r'offerdetails', OfferDetailViewSet, basename='offerdetail')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'reviews', ReviewViewSet, basename='review')

urlpatterns = [
    path('login/', login_view, name='login'),
    path('registration/', registration_view, name='registration'),
    path('profile/<int:pk>/', ProfileDetailView.as_view(), name='profile-detail'),
    path('order-count/<int:business_user_id>/', order_count_view, name='order-count'),
    path('completed-order-count/<int:business_user_id>/', completed_order_count_view, name='completed-order-count'),
    path('base-info/', base_info_view, name='base-info'),
    path('profiles/business/', UserProfileViewSet.as_view({'get': 'business_profiles'}), name='business-profiles'),
    path('profiles/customer/', UserProfileViewSet.as_view({'get': 'customer_profile'}), name='customer-profiles'),
    path('', include(router.urls)),
]