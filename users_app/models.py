"""
User models for Coderr platform.

This module defines user-related models including UserProfile.
"""

from django.contrib.auth.models import User
from django.db import models


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

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
        ordering = ['-created_at']

    def __str__(self):
        """Return string representation of UserProfile."""
        return f"{self.user.username} - {self.type}"