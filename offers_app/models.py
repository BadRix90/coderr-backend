"""
Offer models for Coderr platform.

This module defines offer-related models including Offer and OfferDetail.
"""

from django.contrib.auth.models import User
from django.db import models


class Offer(models.Model):
    """
    Service offer created by business users.
    
    Represents a service that can be purchased by customers.
    Each offer can have multiple pricing tiers (OfferDetail).
    
    Attributes:
        creator (ForeignKey): Business user who created the offer
        title (CharField): Offer title/name
        image (ImageField): Offer preview image
        description (TextField): Detailed offer description
        created_at (DateTimeField): Creation timestamp
        updated_at (DateTimeField): Last update timestamp
    """
    
    creator = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='offers'
    )
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='offers/', null=True, blank=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Offer'
        verbose_name_plural = 'Offers'
        ordering = ['-created_at']

    def __str__(self):
        """Return string representation of Offer."""
        return self.title


class OfferDetail(models.Model):
    """
    Pricing tier for an offer (Basic, Standard, Premium).
    
    Defines specific pricing, delivery time, revisions, and features
    for one tier of an offer.
    
    Attributes:
        offer (ForeignKey): Parent offer
        title (CharField): Tier title (e.g., "Basic Package")
        revisions (IntegerField): Number of revisions included
        delivery_time_in_days (IntegerField): Delivery timeframe
        price (DecimalField): Price for this tier
        features (JSONField): List of included features
        offer_type (CharField): Tier type - 'basic', 'standard', or 'premium'
    """
    
    OFFER_TYPE_CHOICES = [
        ('basic', 'Basic'),
        ('standard', 'Standard'),
        ('premium', 'Premium'),
    ]
    
    offer = models.ForeignKey(
        Offer, 
        on_delete=models.CASCADE, 
        related_name='details'
    )
    title = models.CharField(max_length=200)
    revisions = models.IntegerField()
    delivery_time_in_days = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    features = models.JSONField(default=list)
    offer_type = models.CharField(max_length=10, choices=OFFER_TYPE_CHOICES)

    class Meta:
        verbose_name = 'Offer Detail'
        verbose_name_plural = 'Offer Details'
        ordering = ['offer', 'offer_type']

    def __str__(self):
        """Return string representation of OfferDetail."""
        return f"{self.offer.title} - {self.offer_type}"