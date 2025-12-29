"""
URL configuration for reviews_app API.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ReviewViewSet, base_info_view

# Router for ViewSets
router = DefaultRouter()
router.register(r'reviews', ReviewViewSet, basename='reviews')

urlpatterns = [
    # Base info endpoint
    path('base-info/', base_info_view, name='base-info'),
    
    # Router URLs
    path('', include(router.urls)),
]
