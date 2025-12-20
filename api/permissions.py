"""
Custom permissions for Coderr API.

This module defines permission classes for fine-grained access control
beyond Django's default IsAuthenticated/AllowAny permissions.
"""

from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners to edit objects.

    Read permissions are allowed to any authenticated user,
    but write permissions are only allowed to the owner.
    """

    def has_object_permission(self, request, view, obj):
        """
        Check if user has permission to access the object.

        Args:
            request: The request being made
            view: The view being accessed
            obj: The object being accessed

        Returns:
            bool: True if permission granted, False otherwise
        """
        # Read permissions for safe methods (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only for owner
        # Check if object has 'user' attribute (UserProfile)
        if hasattr(obj, 'user'):
            return obj.user == request.user

        # Check if object has 'creator' attribute (Offer)
        if hasattr(obj, 'creator'):
            return obj.creator == request.user

        # Check if object has 'buyer' attribute (Order)
        if hasattr(obj, 'buyer'):
            return obj.buyer == request.user

        # Check if object has 'reviewer' attribute (Review)
        if hasattr(obj, 'reviewer'):
            return obj.reviewer == request.user

        # Default: deny access
        return False


class IsBusinessUser(permissions.BasePermission):
    """
    Permission to only allow business users.

    Checks if authenticated user has a business-type profile.
    """

    message = 'Only business users can perform this action.'

    def has_permission(self, request, view):
        """
        Check if user is a business user.

        Args:
            request: The request being made
            view: The view being accessed

        Returns:
            bool: True if user is business type, False otherwise
        """
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has profile and is business type
        return (
            hasattr(request.user, 'profile') and
            request.user.profile.type == 'business'
        )


class IsCustomerUser(permissions.BasePermission):
    """
    Permission to only allow customer users.

    Checks if authenticated user has a customer-type profile.
    """

    message = 'Only customer users can perform this action.'

    def has_permission(self, request, view):
        """
        Check if user is a customer user.

        Args:
            request: The request being made
            view: The view being accessed

        Returns:
            bool: True if user is customer type, False otherwise
        """
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has profile and is customer type
        return (
            hasattr(request.user, 'profile') and
            request.user.profile.type == 'customer'
        )


class IsOfferCreatorOrReadOnly(permissions.BasePermission):
    """
    Permission for offer-specific access control.

    - Anyone can view offers (GET)
    - Only the creator can modify/delete their offers
    """

    def has_object_permission(self, request, view, obj):
        """
        Check offer-specific permissions.

        Args:
            request: The request being made
            view: The view being accessed
            obj: The Offer object

        Returns:
            bool: True if permission granted, False otherwise
        """
        # Read permissions allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only for creator
        return obj.creator == request.user


class IsReviewerOrReadOnly(permissions.BasePermission):
    """
    Permission for review-specific access control.

    - Anyone can view reviews (GET)
    - Only the reviewer can modify/delete their reviews
    """

    def has_object_permission(self, request, view, obj):
        """
        Check review-specific permissions.

        Args:
            request: The request being made
            view: The view being accessed
            obj: The Review object

        Returns:
            bool: True if permission granted, False otherwise
        """
        # Read permissions allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only for reviewer
        return obj.reviewer == request.user


class IsOrderBuyerOrReadOnly(permissions.BasePermission):
    """
    Permission for order-specific access control.

    - Only the buyer can view their own orders
    - Only the buyer can update order status
    """

    def has_object_permission(self, request, view, obj):
        """
        Check order-specific permissions.

        Args:
            request: The request being made
            view: The view being accessed
            obj: The Order object

        Returns:
            bool: True if permission granted, False otherwise
        """
        # All operations only for buyer
        return obj.buyer == request.user