from django.contrib import admin
from .models import UserProfile, Offer, OfferDetail, Order, Review


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'type', 'location', 'created_at']
    list_filter = ['type', 'created_at']
    search_fields = ['user__username', 'location']


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ['title', 'creator', 'created_at']
    list_filter = ['created_at']
    search_fields = ['title', 'description', 'creator__username']


@admin.register(OfferDetail)
class OfferDetailAdmin(admin.ModelAdmin):
    list_display = ['offer', 'offer_type', 'price', 'delivery_time_in_days']
    list_filter = ['offer_type']
    search_fields = ['offer__title']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'buyer', 'offer_detail', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['buyer__username']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['reviewer', 'business_user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['reviewer__username', 'business_user__username']