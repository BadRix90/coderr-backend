"""
Django admin configuration for Coderr models.

Registers all models with customized admin interfaces including
list displays, filters, and search fields.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import Offer, OfferDetail, Order, Review, UserProfile


class UserProfileInline(admin.StackedInline):
    """
    Inline admin for UserProfile within User admin.
    
    Allows editing UserProfile fields directly in the User admin interface.
    """
    
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


class UserAdmin(BaseUserAdmin):
    """
    Extended User admin with UserProfile inline.
    
    Adds UserProfile fields to the standard Django User admin.
    """
    
    inlines = (UserProfileInline,)


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin interface for UserProfile model.
    
    Provides list display with user, type, location, and tel fields.
    Includes filters and search functionality.
    """
    
    list_display = ['user', 'type', 'location', 'tel', 'created_at']
    list_filter = ['type', 'created_at']
    search_fields = ['user__username', 'location', 'tel']


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    """
    Admin interface for Offer model.
    
    Shows title, creator, and creation date in list view.
    Enables search by title, description, and creator username.
    """
    
    list_display = ['title', 'creator', 'created_at']
    list_filter = ['created_at']
    search_fields = ['title', 'description', 'creator__username']


@admin.register(OfferDetail)
class OfferDetailAdmin(admin.ModelAdmin):
    """
    Admin interface for OfferDetail model.
    
    Displays offer, type, price, and delivery time.
    Filterable by offer type.
    """
    
    list_display = ['offer', 'offer_type', 'price', 'delivery_time_in_days']
    list_filter = ['offer_type']
    search_fields = ['offer__title']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Admin interface for Order model.
    
    Shows order ID, buyer, offer detail, status, and creation date.
    Filterable by status and creation date.
    """
    
    list_display = ['id', 'buyer', 'offer_detail', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['buyer__username']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """
    Admin interface for Review model.
    
    Displays reviewer, business user, rating, and creation date.
    Filterable by rating and creation date.
    """
    
    list_display = ['reviewer', 'business_user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['reviewer__username', 'business_user__username']