"""
URL configuration for users_app API.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    login_view,
    registration_view,
    ProfileDetailView,
    UserProfileViewSet,
)

# Router for ViewSets
router = DefaultRouter()
router.register(r'profiles', UserProfileViewSet, basename='profiles')

urlpatterns = [
    # Auth endpoints
    path('login/', login_view, name='login'),
    path('registration/', registration_view, name='registration'),
    
    # Profile detail endpoint
    path('profile/<int:pk>/', ProfileDetailView.as_view(), name='profile-detail'),
    
    # Router URLs (profiles/business/, profiles/customer/)
    path('', include(router.urls)),
]