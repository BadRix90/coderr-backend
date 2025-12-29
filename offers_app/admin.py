"""
Admin configuration for offers_app.
"""

from django.contrib import admin

from .models import Offer, OfferDetail


class OfferDetailInline(admin.TabularInline):
    """Inline admin for OfferDetail."""
    
    model = OfferDetail
    extra = 3
    fields = ['title', 'offer_type', 'price', 'delivery_time_in_days', 'revisions']


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    """Admin interface for Offer."""
    
    list_display = ['title', 'creator', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['title', 'description', 'creator__username']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [OfferDetailInline]
    
    fieldsets = (
        ('Offer Information', {
            'fields': ('creator', 'title', 'description', 'image')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(OfferDetail)
class OfferDetailAdmin(admin.ModelAdmin):
    """Admin interface for OfferDetail."""
    
    list_display = [
        'offer', 'offer_type', 'title', 'price', 
        'delivery_time_in_days', 'revisions'
    ]
    list_filter = ['offer_type']
    search_fields = ['title', 'offer__title']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('offer', 'title', 'offer_type')
        }),
        ('Pricing & Delivery', {
            'fields': ('price', 'delivery_time_in_days', 'revisions')
        }),
        ('Features', {
            'fields': ('features',)
        }),
    )