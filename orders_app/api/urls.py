"""
URL configuration for orders_app API.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    OrderViewSet,
    order_count_view,
    completed_order_count_view,
)

# Router for ViewSets
router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='orders')

urlpatterns = [
    # Order count endpoints
    path(
        'order-count/<int:business_user_id>/', 
        order_count_view, 
        name='order-count'
    ),
    path(
        'completed-order-count/<int:business_user_id>/', 
        completed_order_count_view, 
        name='completed-order-count'
    ),
    
    # Router URLs
    path('', include(router.urls)),
]
