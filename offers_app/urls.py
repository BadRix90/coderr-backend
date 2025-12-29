"""
URL configuration for offers_app API.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import OfferViewSet, OfferDetailViewSet

# Router for ViewSets
router = DefaultRouter()
router.register(r'offers', OfferViewSet, basename='offers')
router.register(r'offerdetails', OfferDetailViewSet, basename='offerdetails')

urlpatterns = [
    path('', include(router.urls)),
]