"""
Order models for Coderr platform.

This module defines order-related models.
"""

from django.contrib.auth.models import User
from django.db import models

from offers_app.models import OfferDetail


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
        ('cancelled', 'Cancelled'),
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

    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']

    def __str__(self):
        """Return string representation of Order."""
        return f"Order {self.id} - {self.buyer.username}"