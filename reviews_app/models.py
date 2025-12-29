"""
Review models for Coderr platform.

This module defines review-related models.
"""

from django.contrib.auth.models import User
from django.db import models


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

    class Meta:
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        ordering = ['-created_at']
        unique_together = ['reviewer', 'business_user']

    def __str__(self):
        """Return string representation of Review."""
        return f"Review by {self.reviewer.username} for {self.business_user.username}"