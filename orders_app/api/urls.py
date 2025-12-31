"""
URL configuration for orders_app API.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    OrderViewSet,
    OrderCountView,
    CompletedOrderCountView,
)

# Router for ViewSets
router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='orders')

urlpatterns = [
    # Order count endpoints - GENERIC VIEWS
    path(
        'order-count/<int:business_user_id>/', 
        OrderCountView.as_view(), 
        name='order-count'
    ),
    path(
        'completed-order-count/<int:business_user_id>/', 
        CompletedOrderCountView.as_view(), 
        name='completed-order-count'
    ),
    
    # Router URLs
    path('', include(router.urls)),
]