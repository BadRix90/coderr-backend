# Coderr Backend

Django REST API for Coderr - A Freelancer Platform

## Tech Stack

- Django 6.0
- Django REST Framework 3.16.1
- Django CORS Headers 4.9.0
- Pillow 12.0.0
- SQLite (Development)

## Features

- Token-based Authentication
- User Profiles (Customer & Business)
- Offers with multiple pricing tiers (Basic, Standard, Premium)
- Orders Management
- Reviews & Ratings
- Pagination & Filtering

## Installation
```bash
# Clone repository
git clone https://github.com/BadRix90/coderr-backend.git
cd coderr-backend

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

## API Endpoints

### Authentication
- `POST /api/login/` - User login
- `POST /api/registration/` - User registration

### Profiles
- `GET /api/profile/{id}/` - Get user profile
- `PATCH /api/profile/{id}/` - Update user profile
- `GET /api/profiles/business/` - List business profiles
- `GET /api/profiles/customer/` - List customer profiles

### Offers
- `GET /api/offers/` - List offers (with pagination & filters)
- `POST /api/offers/` - Create offer
- `GET /api/offers/{id}/` - Get offer details
- `PATCH /api/offers/{id}/` - Update offer
- `DELETE /api/offers/{id}/` - Delete offer
- `GET /api/offerdetails/{id}/` - Get offer detail

### Orders
- `GET /api/orders/` - List user's orders
- `POST /api/orders/` - Create order
- `PATCH /api/orders/{id}/` - Update order status
- `GET /api/order-count/{user_id}/` - Get in-progress order count
- `GET /api/completed-order-count/{user_id}/` - Get completed order count

### Reviews
- `GET /api/reviews/` - List reviews (with filters)
- `POST /api/reviews/` - Create review
- `PATCH /api/reviews/{id}/` - Update review

### Stats
- `GET /api/base-info/` - Get platform statistics

## Testing with Postman

Import the included Postman collection and environment:
- `Coderr API.postman_collection.json`
- `Coderr Local.postman_environment.json`

### Test Credentials
- **Customer:** `andrey` / `asdasd`
- **Business:** `kevin` / `asdasd24`
- **Admin:** `Admin` / `Test1234`

## Project Structure
```
backend/
├── api/                    # Main API app
│   ├── models.py          # Database models
│   ├── serializers.py     # DRF serializers
│   ├── views.py           # API views
│   └── urls.py            # API routes
├── coderr/                # Django project settings
│   ├── settings.py        # Configuration
│   └── urls.py            # Root URLs
├── manage.py              # Django management
└── requirements.txt       # Dependencies
```

## License

This is a portfolio project for educational purposes.