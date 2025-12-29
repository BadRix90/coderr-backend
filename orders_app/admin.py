"""
Admin configuration for orders_app.
"""

from django.contrib import admin

from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin interface for Order."""
    
    list_display = [
        'id', 'buyer', 'get_offer_title', 'get_business_user', 
        'status', 'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = [
        'buyer__username', 'offer_detail__offer__title',
        'offer_detail__offer__creator__username'
    ]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('buyer', 'offer_detail', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_offer_title(self, obj):
        """Get offer title."""
        return obj.offer_detail.offer.title
    get_offer_title.short_description = 'Offer'
    
    def get_business_user(self, obj):
        """Get business user."""
        return obj.offer_detail.offer.creator.username
    get_business_user.short_description = 'Business User'