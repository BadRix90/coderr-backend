"""
Comprehensive test suite for Coderr API.

This module contains tests for models, serializers, views, and API endpoints
to achieve >95% test coverage as required by the project checklist.

CORRECTED to match Postman Collection specification.
"""

from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIRequestFactory, APITestCase, force_authenticate

from .models import Offer, OfferDetail, Order, Review, UserProfile
from .permissions import (
    IsBusinessUser,
    IsCustomerUser,
    IsOfferCreatorOrReadOnly,
    IsOrderBuyerOrReadOnly,
    IsOwnerOrReadOnly,
    IsReviewerOrReadOnly,
)


# =============================================================================
# MODEL TESTS
# =============================================================================

class UserProfileModelTest(TestCase):
    """Test cases for UserProfile model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            type='customer',
            location='Berlin',
            description='Test description'
        )

    def test_profile_creation(self):
        """Test UserProfile is created correctly."""
        self.assertEqual(self.profile.user, self.user)
        self.assertEqual(self.profile.type, 'customer')
        self.assertEqual(self.profile.location, 'Berlin')

    def test_profile_str_method(self):
        """Test UserProfile __str__ method."""
        expected = f"{self.user.username} - {self.profile.type}"
        self.assertEqual(str(self.profile), expected)

    def test_profile_type_choices(self):
        """Test UserProfile type choices."""
        self.assertIn(self.profile.type, ['customer', 'business'])


class OfferModelTest(TestCase):
    """Test cases for Offer model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='business',
            password='testpass123'
        )
        UserProfile.objects.create(user=self.user, type='business')
        self.offer = Offer.objects.create(
            creator=self.user,
            title='Test Offer',
            description='Test Description'
        )

    def test_offer_creation(self):
        """Test Offer is created correctly."""
        self.assertEqual(self.offer.creator, self.user)
        self.assertEqual(self.offer.title, 'Test Offer')
        self.assertIsNotNone(self.offer.created_at)

    def test_offer_str_method(self):
        """Test Offer __str__ method."""
        self.assertEqual(str(self.offer), 'Test Offer')


class OfferDetailModelTest(TestCase):
    """Test cases for OfferDetail model."""

    def setUp(self):
        """Set up test data."""
        user = User.objects.create_user(username='business', password='test')
        UserProfile.objects.create(user=user, type='business')
        self.offer = Offer.objects.create(
            creator=user,
            title='Test',
            description='Test'
        )
        self.detail = OfferDetail.objects.create(
            offer=self.offer,
            title='Basic Package',
            revisions=2,
            delivery_time_in_days=7,
            price=Decimal('299.99'),
            features=['Feature 1', 'Feature 2'],
            offer_type='basic'
        )

    def test_offer_detail_creation(self):
        """Test OfferDetail is created correctly."""
        self.assertEqual(self.detail.offer, self.offer)
        self.assertEqual(self.detail.price, Decimal('299.99'))
        self.assertEqual(len(self.detail.features), 2)

    def test_offer_detail_str_method(self):
        """Test OfferDetail __str__ method."""
        expected = f"{self.offer.title} - {self.detail.offer_type}"
        self.assertEqual(str(self.detail), expected)


class OrderModelTest(TestCase):
    """Test cases for Order model."""

    def setUp(self):
        """Set up test data."""
        business_user = User.objects.create_user(
            username='business',
            password='test'
        )
        UserProfile.objects.create(user=business_user, type='business')

        buyer = User.objects.create_user(username='customer', password='test')
        UserProfile.objects.create(user=buyer, type='customer')

        offer = Offer.objects.create(
            creator=business_user,
            title='Test',
            description='Test'
        )
        self.detail = OfferDetail.objects.create(
            offer=offer,
            title='Basic',
            revisions=2,
            delivery_time_in_days=7,
            price=Decimal('299.99'),
            offer_type='basic'
        )
        self.order = Order.objects.create(
            buyer=buyer,
            offer_detail=self.detail,
            status='in_progress'
        )

    def test_order_creation(self):
        """Test Order is created correctly."""
        self.assertEqual(self.order.status, 'in_progress')
        self.assertEqual(self.order.offer_detail, self.detail)
        self.assertIsNotNone(self.order.created_at)

    def test_order_str_method(self):
        """Test Order __str__ method."""
        expected = f"Order {self.order.id} - {self.order.buyer.username}"
        self.assertEqual(str(self.order), expected)


class ReviewModelTest(TestCase):
    """Test cases for Review model."""

    def setUp(self):
        """Set up test data."""
        self.reviewer = User.objects.create_user(
            username='customer',
            password='test'
        )
        UserProfile.objects.create(user=self.reviewer, type='customer')

        self.business = User.objects.create_user(
            username='business',
            password='test'
        )
        UserProfile.objects.create(user=self.business, type='business')

        self.review = Review.objects.create(
            reviewer=self.reviewer,
            business_user=self.business,
            rating=5,
            description='Excellent!'
        )

    def test_review_creation(self):
        """Test Review is created correctly."""
        self.assertEqual(self.review.rating, 5)
        self.assertEqual(self.review.reviewer, self.reviewer)
        self.assertEqual(self.review.business_user, self.business)

    def test_review_str_method(self):
        """Test Review __str__ method."""
        expected = (
            f"Review by {self.reviewer.username} "
            f"for {self.business.username}"
        )
        self.assertEqual(str(self.review), expected)


# =============================================================================
# API TESTS
# =============================================================================

class AuthenticationAPITest(APITestCase):
    """Test cases for authentication endpoints."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@test.com'
        )
        UserProfile.objects.create(user=self.user, type='customer')

    def test_registration_success(self):
        """Test user registration with valid data."""
        data = {
            'username': 'newuser',
            'email': 'new@test.com',
            'password': 'newpass123',
            'repeated_password': 'newpass123',  # FIX: Added repeated_password
            'type': 'customer'
        }
        response = self.client.post('/api/registration/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_registration_duplicate_username(self):
        """Test registration with existing username fails."""
        data = {
            'username': 'testuser',
            'email': 'another@test.com',
            'password': 'pass123',
            'repeated_password': 'pass123',  # FIX: Added repeated_password
            'type': 'customer'
        }
        response = self.client.post('/api/registration/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        """Test login with valid credentials."""
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post('/api/login/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials fails."""
        data = {
            'username': 'testuser',
            'password': 'wrongpass'
        }
        response = self.client.post('/api/login/', data)
        # FIX: Changed from 401 to 400 (matches Postman spec and views.py)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserProfileAPITest(APITestCase):
    """Test cases for UserProfile API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            type='customer'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_get_profile(self):
        """Test retrieving user profile."""
        # FIX: Use user.id not profile.id (per endpoint doc)
        response = self.client.get(f'/api/profile/{self.user.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')

    def test_update_profile(self):
        """Test updating user profile."""
        data = {'location': 'Munich', 'description': 'Updated'}
        response = self.client.patch(
            f'/api/profile/{self.user.id}/',  # FIX: Use user.id
            data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.location, 'Munich')

    def test_business_profiles_list(self):
        """Test listing business profiles."""
        User.objects.create_user(username='business1', password='test')
        UserProfile.objects.create(
            user=User.objects.get(username='business1'),
            type='business'
        )
        response = self.client.get('/api/profiles/business/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_customer_profiles_list(self):
        """Test listing customer profiles."""
        response = self.client.get('/api/profiles/customer/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)


class OfferAPITest(APITestCase):
    """Test cases for Offer API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.business_user = User.objects.create_user(
            username='business',
            password='testpass123'
        )
        UserProfile.objects.create(
            user=self.business_user,
            type='business'
        )
        self.token = Token.objects.create(user=self.business_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

        # FIX: Must have exactly 3 details (basic, standard, premium)
        self.offer_data = {
            'title': 'Web Development',
            'description': 'Professional web dev',
            'details': [
                {
                    'title': 'Basic Package',
                    'revisions': 2,
                    'delivery_time_in_days': 7,
                    'price': '299.99',
                    'features': ['Feature 1'],
                    'offer_type': 'basic'
                },
                {
                    'title': 'Standard Package',
                    'revisions': 5,
                    'delivery_time_in_days': 14,
                    'price': '599.99',
                    'features': ['Feature 1', 'Feature 2'],
                    'offer_type': 'standard'
                },
                {
                    'title': 'Premium Package',
                    'revisions': -1,
                    'delivery_time_in_days': 21,
                    'price': '999.99',
                    'features': ['Feature 1', 'Feature 2', 'Feature 3'],
                    'offer_type': 'premium'
                }
            ]
        }

    def test_create_offer(self):
        """Test creating an offer."""
        response = self.client.post('/api/offers/', self.offer_data, format='json')
        if response.status_code != status.HTTP_201_CREATED:
            print(f"Error: {response.data}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Offer.objects.count(), 1)
        self.assertEqual(OfferDetail.objects.count(), 3)  # FIX: 3 details

    def test_list_offers(self):
        """Test listing offers."""
        self.client.post('/api/offers/', self.offer_data, format='json')
        response = self.client.get('/api/offers/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if paginated response
        if isinstance(response.data, dict) and 'results' in response.data:
            self.assertGreaterEqual(len(response.data['results']), 1)
        else:
            self.assertGreaterEqual(len(response.data), 1)

    def test_filter_offers_by_creator(self):
        """Test filtering offers by creator."""
        self.client.post('/api/offers/', self.offer_data, format='json')
        response = self.client.get(
            f'/api/offers/?creator_id={self.business_user.id}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        if isinstance(response.data, dict) and 'results' in response.data:
            self.assertGreaterEqual(len(response.data['results']), 1)
        else:
            self.assertGreaterEqual(len(response.data), 1)

    def test_update_offer(self):
        """Test updating an offer."""
        create_response = self.client.post('/api/offers/', self.offer_data, format='json')
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        offer_id = create_response.data['id']

        update_data = {
            'title': 'Updated Title',
            'description': 'Updated Description',
            'details': self.offer_data['details']
        }
        response = self.client.patch(f'/api/offers/{offer_id}/', update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Title')

    def test_delete_offer(self):
        """Test deleting an offer."""
        create_response = self.client.post('/api/offers/', self.offer_data, format='json')
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        offer_id = create_response.data['id']

        response = self.client.delete(f'/api/offers/{offer_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Offer.objects.count(), 0)


class OrderAPITest(APITestCase):
    """Test cases for Order API endpoints."""

    def setUp(self):
        """Set up test data."""
        # Create business user and offer
        self.business = User.objects.create_user(
            username='business',
            password='test'
        )
        UserProfile.objects.create(user=self.business, type='business')
        self.business_token = Token.objects.create(user=self.business)

        offer = Offer.objects.create(
            creator=self.business,
            title='Test Offer',
            description='Test'
        )
        self.offer_detail = OfferDetail.objects.create(
            offer=offer,
            title='Basic',
            revisions=2,
            delivery_time_in_days=7,
            price=Decimal('299.99'),
            offer_type='basic'
        )

        # Create customer user
        self.customer = User.objects.create_user(
            username='customer',
            password='test'
        )
        UserProfile.objects.create(user=self.customer, type='customer')
        self.customer_token = Token.objects.create(user=self.customer)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.customer_token.key}')

    def test_create_order(self):
        """Test creating an order."""
        data = {
            'offer_detail_id': self.offer_detail.id,
            'status': 'in_progress'
        }
        response = self.client.post('/api/orders/', data, format='json')
        if response.status_code != status.HTTP_201_CREATED:
            print(f"Order creation error: {response.data}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)

    def test_list_user_orders(self):
        """Test listing user's orders."""
        Order.objects.create(
            buyer=self.customer,
            offer_detail=self.offer_detail,
            status='in_progress'
        )
        response = self.client.get('/api/orders/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # No pagination for orders per doc
        self.assertEqual(len(response.data), 1)

    def test_update_order_status(self):
        """Test updating order status."""
        order = Order.objects.create(
            buyer=self.customer,
            offer_detail=self.offer_detail,
            status='in_progress'
        )
        
        # FIX: Only business (offer creator) can update order status
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.business_token.key}')
        
        data = {'status': 'completed'}
        response = self.client.patch(f'/api/orders/{order.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.status, 'completed')


class ReviewAPITest(APITestCase):
    """Test cases for Review API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.business = User.objects.create_user(
            username='business',
            password='test'
        )
        UserProfile.objects.create(user=self.business, type='business')

        self.customer = User.objects.create_user(
            username='customer',
            password='test'
        )
        UserProfile.objects.create(user=self.customer, type='customer')

        self.token = Token.objects.create(user=self.customer)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_create_review(self):
        """Test creating a review."""
        data = {
            'business_user': self.business.id,
            'rating': 5,
            'description': 'Excellent work!'
        }
        response = self.client.post('/api/reviews/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Review.objects.count(), 1)

    def test_list_reviews(self):
        """Test listing reviews."""
        Review.objects.create(
            reviewer=self.customer,
            business_user=self.business,
            rating=5,
            description='Great!'
        )
        response = self.client.get('/api/reviews/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # No pagination for reviews per doc
        self.assertGreaterEqual(len(response.data), 1)

    def test_filter_reviews_by_business_user(self):
        """Test filtering reviews by business user."""
        Review.objects.create(
            reviewer=self.customer,
            business_user=self.business,
            rating=5,
            description='Great!'
        )
        response = self.client.get(
            f'/api/reviews/?business_user_id={self.business.id}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)


class StatisticsAPITest(APITestCase):
    """Test cases for statistics endpoints."""

    def setUp(self):
        """Set up test data."""
        business = User.objects.create_user(username='business', password='test')
        self.business_profile = UserProfile.objects.create(
            user=business,
            type='business'
        )

        customer = User.objects.create_user(username='customer', password='test')
        UserProfile.objects.create(user=customer, type='customer')

        offer = Offer.objects.create(
            creator=business,
            title='Test',
            description='Test'
        )
        detail = OfferDetail.objects.create(
            offer=offer,
            title='Basic',
            revisions=2,
            delivery_time_in_days=7,
            price=Decimal('299.99'),
            offer_type='basic'
        )

        Order.objects.create(
            buyer=customer,
            offer_detail=detail,
            status='in_progress'
        )
        Order.objects.create(
            buyer=customer,
            offer_detail=detail,
            status='completed'
        )

        self.token = Token.objects.create(user=customer)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_order_count(self):
        """Test order count endpoint."""
        response = self.client.get(
            f'/api/order-count/{self.business_profile.user.id}/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['order_count'], 1)

    def test_completed_order_count(self):
        """Test completed order count endpoint."""
        response = self.client.get(
            f'/api/completed-order-count/{self.business_profile.user.id}/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # FIX: Field name is 'completed_order_count' not 'order_count'
        self.assertEqual(response.data['completed_order_count'], 1)

    def test_base_info(self):
        """Test base info endpoint."""
        response = self.client.get('/api/base-info/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # FIX: Correct field names per Postman spec
        self.assertIn('review_count', response.data)
        self.assertIn('average_rating', response.data)
        self.assertIn('business_profile_count', response.data)
        self.assertIn('offer_count', response.data)


# =============================================================================
# PERMISSION TESTS
# =============================================================================

class IsOwnerOrReadOnlyPermissionTest(TestCase):
    """Test cases for IsOwnerOrReadOnly permission."""

    def setUp(self):
        """Set up test data."""
        self.factory = APIRequestFactory()
        self.permission = IsOwnerOrReadOnly()

        self.owner = User.objects.create_user(
            username='owner',
            password='test'
        )
        self.other_user = User.objects.create_user(
            username='other',
            password='test'
        )

        self.profile = UserProfile.objects.create(
            user=self.owner,
            type='customer'
        )

        self.offer = Offer.objects.create(
            creator=self.owner,
            title='Test',
            description='Test'
        )

        self.review = Review.objects.create(
            reviewer=self.owner,
            business_user=self.other_user,
            rating=5,
            description='Great!'
        )

    def test_read_allowed_for_safe_methods(self):
        """Test that read operations are allowed."""
        request = self.factory.get('/api/test/')
        request.user = self.other_user
        has_permission = self.permission.has_object_permission(
            request,
            None,
            self.profile
        )
        self.assertTrue(has_permission)

    def test_owner_can_modify_profile(self):
        """Test that owner can modify their profile."""
        request = self.factory.patch('/api/test/')
        request.user = self.owner
        has_permission = self.permission.has_object_permission(
            request,
            None,
            self.profile
        )
        self.assertTrue(has_permission)

    def test_non_owner_cannot_modify(self):
        """Test that non-owner cannot modify."""
        request = self.factory.patch('/api/test/')
        request.user = self.other_user
        has_permission = self.permission.has_object_permission(
            request,
            None,
            self.profile
        )
        self.assertFalse(has_permission)


class IsBusinessUserPermissionTest(TestCase):
    """Test cases for IsBusinessUser permission."""

    def setUp(self):
        """Set up test data."""
        self.factory = APIRequestFactory()
        self.permission = IsBusinessUser()

        self.business_user = User.objects.create_user(
            username='business',
            password='test'
        )
        UserProfile.objects.create(
            user=self.business_user,
            type='business'
        )

        self.customer_user = User.objects.create_user(
            username='customer',
            password='test'
        )
        UserProfile.objects.create(
            user=self.customer_user,
            type='customer'
        )

    def test_business_user_has_permission(self):
        """Test that business users have permission."""
        request = self.factory.get('/api/test/')
        request.user = self.business_user
        has_permission = self.permission.has_permission(request, None)
        self.assertTrue(has_permission)

    def test_customer_user_no_permission(self):
        """Test that customer users don't have permission."""
        request = self.factory.get('/api/test/')
        request.user = self.customer_user
        has_permission = self.permission.has_permission(request, None)
        self.assertFalse(has_permission)

    def test_unauthenticated_no_permission(self):
        """Test that unauthenticated users don't have permission."""
        request = self.factory.get('/api/test/')
        request.user = None
        has_permission = self.permission.has_permission(request, None)
        self.assertFalse(has_permission)


class IsCustomerUserPermissionTest(TestCase):
    """Test cases for IsCustomerUser permission."""

    def setUp(self):
        """Set up test data."""
        self.factory = APIRequestFactory()
        self.permission = IsCustomerUser()

        self.business_user = User.objects.create_user(
            username='business',
            password='test'
        )
        UserProfile.objects.create(
            user=self.business_user,
            type='business'
        )

        self.customer_user = User.objects.create_user(
            username='customer',
            password='test'
        )
        UserProfile.objects.create(
            user=self.customer_user,
            type='customer'
        )

    def test_customer_user_has_permission(self):
        """Test that customer users have permission."""
        request = self.factory.get('/api/test/')
        request.user = self.customer_user
        has_permission = self.permission.has_permission(request, None)
        self.assertTrue(has_permission)

    def test_business_user_no_permission(self):
        """Test that business users don't have permission."""
        request = self.factory.get('/api/test/')
        request.user = self.business_user
        has_permission = self.permission.has_permission(request, None)
        self.assertFalse(has_permission)

    def test_unauthenticated_no_permission(self):
        """Test that unauthenticated users don't have permission."""
        request = self.factory.get('/api/test/')
        request.user = None
        has_permission = self.permission.has_permission(request, None)
        self.assertFalse(has_permission)


class IsOfferCreatorOrReadOnlyPermissionTest(TestCase):
    """Test cases for IsOfferCreatorOrReadOnly permission."""

    def setUp(self):
        """Set up test data."""
        self.factory = APIRequestFactory()
        self.permission = IsOfferCreatorOrReadOnly()

        self.creator = User.objects.create_user(
            username='creator',
            password='test'
        )
        self.other_user = User.objects.create_user(
            username='other',
            password='test'
        )

        self.offer = Offer.objects.create(
            creator=self.creator,
            title='Test',
            description='Test'
        )

    def test_read_allowed_for_anyone(self):
        """Test that anyone can read offers."""
        request = self.factory.get('/api/offers/1/')
        request.user = self.other_user
        has_permission = self.permission.has_object_permission(
            request,
            None,
            self.offer
        )
        self.assertTrue(has_permission)

    def test_creator_can_modify(self):
        """Test that creator can modify their offer."""
        request = self.factory.patch('/api/offers/1/')
        request.user = self.creator
        has_permission = self.permission.has_object_permission(
            request,
            None,
            self.offer
        )
        self.assertTrue(has_permission)

    def test_non_creator_cannot_modify(self):
        """Test that non-creator cannot modify offer."""
        request = self.factory.patch('/api/offers/1/')
        request.user = self.other_user
        has_permission = self.permission.has_object_permission(
            request,
            None,
            self.offer
        )
        self.assertFalse(has_permission)


class IsReviewerOrReadOnlyPermissionTest(TestCase):
    """Test cases for IsReviewerOrReadOnly permission."""

    def setUp(self):
        """Set up test data."""
        self.factory = APIRequestFactory()
        self.permission = IsReviewerOrReadOnly()

        self.reviewer = User.objects.create_user(
            username='reviewer',
            password='test'
        )
        self.business = User.objects.create_user(
            username='business',
            password='test'
        )
        self.other_user = User.objects.create_user(
            username='other',
            password='test'
        )

        self.review = Review.objects.create(
            reviewer=self.reviewer,
            business_user=self.business,
            rating=5,
            description='Great!'
        )

    def test_read_allowed_for_anyone(self):
        """Test that anyone can read reviews."""
        request = self.factory.get('/api/reviews/1/')
        request.user = self.other_user
        has_permission = self.permission.has_object_permission(
            request,
            None,
            self.review
        )
        self.assertTrue(has_permission)

    def test_reviewer_can_modify(self):
        """Test that reviewer can modify their review."""
        request = self.factory.patch('/api/reviews/1/')
        request.user = self.reviewer
        has_permission = self.permission.has_object_permission(
            request,
            None,
            self.review
        )
        self.assertTrue(has_permission)

    def test_non_reviewer_cannot_modify(self):
        """Test that non-reviewer cannot modify review."""
        request = self.factory.patch('/api/reviews/1/')
        request.user = self.other_user
        has_permission = self.permission.has_object_permission(
            request,
            None,
            self.review
        )
        self.assertFalse(has_permission)


class IsOrderBuyerOrReadOnlyPermissionTest(TestCase):
    """Test cases for IsOrderBuyerOrReadOnly permission."""

    def setUp(self):
        """Set up test data."""
        self.factory = APIRequestFactory()
        self.permission = IsOrderBuyerOrReadOnly()

        self.buyer = User.objects.create_user(
            username='buyer',
            password='test'
        )
        UserProfile.objects.create(user=self.buyer, type='customer')

        self.other_user = User.objects.create_user(
            username='other',
            password='test'
        )
        UserProfile.objects.create(user=self.other_user, type='customer')

        creator = User.objects.create_user(
            username='creator',
            password='test'
        )
        UserProfile.objects.create(user=creator, type='business')

        offer = Offer.objects.create(
            creator=creator,
            title='Test',
            description='Test'
        )
        detail = OfferDetail.objects.create(
            offer=offer,
            title='Basic',
            revisions=2,
            delivery_time_in_days=7,
            price=Decimal('299.99'),
            offer_type='basic'
        )

        self.order = Order.objects.create(
            buyer=self.buyer,
            offer_detail=detail,
            status='in_progress'
        )

    def test_buyer_can_access(self):
        """Test that buyer can access their order."""
        request = self.factory.get('/api/orders/1/')
        request.user = self.buyer
        has_permission = self.permission.has_object_permission(
            request,
            None,
            self.order
        )
        self.assertTrue(has_permission)

    def test_non_buyer_cannot_access(self):
        """Test that non-buyer cannot access order."""
        request = self.factory.get('/api/orders/1/')
        request.user = self.other_user
        has_permission = self.permission.has_object_permission(
            request,
            None,
            self.order
        )
        self.assertFalse(has_permission)

    def test_buyer_can_modify(self):
        """Test that buyer can modify their order."""
        request = self.factory.patch('/api/orders/1/')
        request.user = self.buyer
        has_permission = self.permission.has_object_permission(
            request,
            None,
            self.order
        )
        self.assertTrue(has_permission)