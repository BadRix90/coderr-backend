"""
Django models for Coderr freelancer platform.

This module defines the core data models including UserProfile, Offer,
OfferDetail, Order, and Review.
"""

from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """
    Extended user profile for Coderr platform.
    
    Stores additional information beyond Django's default User model,
    including user type (customer/business), contact details, and metadata.
    
    Attributes:
        user (OneToOneField): Link to Django User model
        type (CharField): User type - 'customer' or 'business'
        file (ImageField): Profile picture/avatar
        location (CharField): User's location/city
        description (TextField): Profile description/bio
        working_hours (CharField): Business working hours
        tel (CharField): Telephone number
        created_at (DateTimeField): Profile creation timestamp
        updated_at (DateTimeField): Last update timestamp
    """
    
    USER_TYPE_CHOICES = [
        ('customer', 'Customer'),
        ('business', 'Business'),
    ]
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='profile'
    )
    type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    file = models.ImageField(upload_to='profiles/', null=True, blank=True)
    location = models.CharField(max_length=100, blank=True, default='')
    description = models.TextField(blank=True, default='')
    working_hours = models.CharField(max_length=50, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tel = models.CharField(max_length=20, blank=True, default='')

    def __str__(self):
        """Return string representation of UserProfile."""
        return f"{self.user.username} - {self.type}"


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

    def __str__(self):
        """Return string representation of OfferDetail."""
        return f"{self.offer.title} - {self.offer_type}"


class Order(models.Model):
    """
    Purchase order from customer to business user.
    
    Represents a customer's purchase of a specific offer tier.
    Tracks order status from in-progress to completed.
    
    Attributes:
        buyer (ForeignKey): Customer who placed the order
        offer_detail (ForeignKey): Purchased offer tier
        status (CharField): Order status - 'in_progress' or 'completed'
        created_at (DateTimeField): Order creation timestamp
        updated_at (DateTimeField): Last update timestamp
    """
    
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]
    
    buyer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='orders'
    )
    offer_detail = models.ForeignKey(
        OfferDetail, 
        on_delete=models.CASCADE, 
        related_name='orders'
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='in_progress'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """Return string representation of Order."""
        return f"Order {self.id} - {self.buyer.username}"


class Review(models.Model):
    """
    Customer review for a business user.
    
    Allows customers to rate and review business users after
    completing an order.
    
    Attributes:
        reviewer (ForeignKey): Customer who wrote the review
        business_user (ForeignKey): Business user being reviewed
        rating (IntegerField): Rating score (typically 1-5)
        description (TextField): Review text/comments
        created_at (DateTimeField): Review creation timestamp
        updated_at (DateTimeField): Last update timestamp
    """
    
    reviewer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='reviews_given'
    )
    business_user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='reviews_received'
    )
    rating = models.IntegerField()
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """Return string representation of Review."""
        return f"Review by {self.reviewer.username} for {self.business_user.username}"
