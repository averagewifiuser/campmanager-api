"""
Pytest configuration and fixtures for CampManager API tests

This module contains shared fixtures and configuration for all tests.
"""

import pytest
import os
import tempfile
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import uuid

from app import create_app
from app.extensions import db
from app.user.models import User
from app.camp.models import Camp, Church, Category, CustomField, RegistrationLink, Registration


@pytest.fixture(scope='session')
def app():
    """Create application for testing"""
    # Create a temporary database file with 'test' in the name
    db_fd, db_path = tempfile.mkstemp(suffix='_test.db')
    
    # Set test configuration
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SECRET_KEY': 'test-secret-key',
        'JWT_SECRET_KEY': 'test-jwt-secret-key',
        'WTF_CSRF_ENABLED': False,
        'JWT_ACCESS_TOKEN_EXPIRES': timedelta(minutes=15),
        'JWT_REFRESH_TOKEN_EXPIRES': timedelta(hours=1)
    }
    
    # Create app with test config
    app = create_app('testing')
    
    # Override config with test values
    app.config.update(test_config)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        yield app
        
        # Cleanup
        db.drop_all()
    
    # Close and remove temporary database
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner"""
    return app.test_cli_runner()


@pytest.fixture
def app_context(app):
    """Create application context"""
    with app.app_context():
        yield app


@pytest.fixture
def db_session(app_context):
    """Create database session for testing"""
    yield db.session
    
    # Clean up after each test
    db.session.rollback()
    # Clear all data from tables
    for table in reversed(db.metadata.sorted_tables):
        db.session.execute(table.delete())
    db.session.commit()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    # Use a unique email for each test to avoid conflicts
    import time
    timestamp = str(int(time.time() * 1000000))  # microsecond timestamp
    return {
        'email': f'test_{timestamp}@example.com',
        'password': 'testpassword123',
        'full_name': 'Test User',
        'role': 'camp_manager'
    }


@pytest.fixture
def sample_user(db_session, sample_user_data):
    """Create a sample user for testing"""
    user = User(
        email=sample_user_data['email'],
        full_name=sample_user_data['full_name'],
        role=sample_user_data['role']
    )
    user.set_password(sample_user_data['password'])
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def sample_volunteer_data():
    """Sample volunteer user data for testing"""
    # Use a unique email for each test to avoid conflicts
    import time
    timestamp = str(int(time.time() * 1000000))  # microsecond timestamp
    return {
        'email': f'volunteer_{timestamp}@example.com',
        'password': 'volunteerpass123',
        'full_name': 'Test Volunteer',
        'role': 'volunteer'
    }


@pytest.fixture
def sample_volunteer(db_session, sample_volunteer_data):
    """Create a sample volunteer user for testing"""
    user = User(
        email=sample_volunteer_data['email'],
        full_name=sample_volunteer_data['full_name'],
        role=sample_volunteer_data['role']
    )
    user.set_password(sample_volunteer_data['password'])
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def sample_camp_data():
    """Sample camp data for testing"""
    return {
        'name': 'Test Summer Camp',
        'start_date': datetime.now(timezone.utc).date() + timedelta(days=30),
        'end_date': datetime.now(timezone.utc).date() + timedelta(days=35),
        'location': 'Test Camp Location',
        'base_fee': Decimal('100.00'),
        'capacity': 100,
        'description': 'A test summer camp for testing purposes',
        'registration_deadline': datetime.now(timezone.utc) + timedelta(days=20)
    }


@pytest.fixture
def sample_camp(db_session, sample_user, sample_camp_data):
    """Create a sample camp for testing"""
    camp = Camp(
        name=sample_camp_data['name'],
        start_date=sample_camp_data['start_date'],
        end_date=sample_camp_data['end_date'],
        location=sample_camp_data['location'],
        base_fee=sample_camp_data['base_fee'],
        capacity=sample_camp_data['capacity'],
        description=sample_camp_data['description'],
        registration_deadline=sample_camp_data['registration_deadline'],
        camp_manager_id=sample_user.id
    )
    db.session.add(camp)
    db.session.commit()
    return camp


@pytest.fixture
def sample_church_data():
    """Sample church data for testing"""
    return {
        'name': 'Test Church'
    }


@pytest.fixture
def sample_church(db_session, sample_camp, sample_church_data):
    """Create a sample church for testing"""
    church = Church(
        name=sample_church_data['name'],
        camp_id=sample_camp.id
    )
    db.session.add(church)
    db.session.commit()
    return church


@pytest.fixture
def sample_category_data():
    """Sample category data for testing"""
    return {
        'name': 'Adult',
        'discount_percentage': Decimal('0.00'),
        'discount_amount': Decimal('0.00'),
        'is_default': True
    }


@pytest.fixture
def sample_category(db_session, sample_camp, sample_category_data):
    """Create a sample category for testing"""
    category = Category(
        name=sample_category_data['name'],
        discount_percentage=sample_category_data['discount_percentage'],
        discount_amount=sample_category_data['discount_amount'],
        is_default=sample_category_data['is_default'],
        camp_id=sample_camp.id
    )
    db.session.add(category)
    db.session.commit()
    return category


@pytest.fixture
def sample_discount_category(db_session, sample_camp):
    """Create a sample category with discount for testing"""
    category = Category(
        name='Student',
        discount_percentage=Decimal('20.00'),
        discount_amount=Decimal('0.00'),
        is_default=False,
        camp_id=sample_camp.id
    )
    db.session.add(category)
    db.session.commit()
    return category


@pytest.fixture
def sample_custom_field_data():
    """Sample custom field data for testing"""
    return {
        'field_name': 'Dietary Restrictions',
        'field_type': 'text',
        'is_required': False,
        'options': None,
        'order': 1
    }


@pytest.fixture
def sample_custom_field(db_session, sample_camp, sample_custom_field_data):
    """Create a sample custom field for testing"""
    custom_field = CustomField(
        field_name=sample_custom_field_data['field_name'],
        field_type=sample_custom_field_data['field_type'],
        is_required=sample_custom_field_data['is_required'],
        options=sample_custom_field_data['options'],
        order=sample_custom_field_data['order'],
        camp_id=sample_camp.id
    )
    db.session.add(custom_field)
    db.session.commit()
    return custom_field


@pytest.fixture
def sample_dropdown_field(db_session, sample_camp):
    """Create a sample dropdown custom field for testing"""
    custom_field = CustomField(
        field_name='T-Shirt Size',
        field_type='dropdown',
        is_required=True,
        options=['S', 'M', 'L', 'XL'],
        order=2,
        camp_id=sample_camp.id
    )
    db.session.add(custom_field)
    db.session.commit()
    return custom_field


@pytest.fixture
def sample_registration_link_data():
    """Sample registration link data for testing"""
    return {
        'name': 'General Registration',
        'is_active': True,
        'expires_at': datetime.now(timezone.utc) + timedelta(days=30),
        'usage_limit': 100,
        'usage_count': 0
    }


@pytest.fixture
def sample_registration_link(db_session, sample_camp, sample_user, sample_category, sample_registration_link_data):
    """Create a sample registration link for testing"""
    registration_link = RegistrationLink(
        name=sample_registration_link_data['name'],
        allowed_categories=[str(sample_category.id)],
        is_active=sample_registration_link_data['is_active'],
        expires_at=sample_registration_link_data['expires_at'],
        usage_limit=sample_registration_link_data['usage_limit'],
        usage_count=sample_registration_link_data['usage_count'],
        camp_id=sample_camp.id,
        created_by=sample_user.id
    )
    db.session.add(registration_link)
    db.session.commit()
    return registration_link


@pytest.fixture
def sample_registration_data():
    """Sample registration data for testing"""
    return {
        'surname': 'John',
        'middle_name': 'Michael',
        'last_name': 'Doe',
        'age': 25,
        'email': 'john.doe@example.com',
        'phone_number': '+1234567890',
        'emergency_contact_name': 'Jane Doe',
        'emergency_contact_phone': '+0987654321',
        'custom_field_responses': {'dietary_restrictions': 'None'},
        'has_paid': False,
        'has_checked_in': False
    }


@pytest.fixture
def sample_registration(db_session, sample_camp, sample_church, sample_category, sample_registration_data):
    """Create a sample registration for testing"""
    registration = Registration(
        surname=sample_registration_data['surname'],
        middle_name=sample_registration_data['middle_name'],
        last_name=sample_registration_data['last_name'],
        age=sample_registration_data['age'],
        email=sample_registration_data['email'],
        phone_number=sample_registration_data['phone_number'],
        emergency_contact_name=sample_registration_data['emergency_contact_name'],
        emergency_contact_phone=sample_registration_data['emergency_contact_phone'],
        custom_field_responses=sample_registration_data['custom_field_responses'],
        total_amount=Decimal('100.00'),
        has_paid=sample_registration_data['has_paid'],
        has_checked_in=sample_registration_data['has_checked_in'],
        camp_id=sample_camp.id,
        church_id=sample_church.id,
        category_id=sample_category.id
    )
    db.session.add(registration)
    db.session.commit()
    return registration


@pytest.fixture
def auth_headers(client, sample_user, sample_user_data):
    """Get authentication headers for testing"""
    # Login to get access token
    response = client.post('/auth/login', json={
        'data': {
            'email': sample_user_data['email'],
            'password': sample_user_data['password']
        }
    })
    
    assert response.status_code == 200
    data = response.get_json()
    access_token = data['data']['access_token']
    
    return {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }


@pytest.fixture
def volunteer_auth_headers(client, sample_volunteer, sample_volunteer_data):
    """Get authentication headers for volunteer user"""
    # Login to get access token
    response = client.post('/auth/login', json={
        'data': {
            'email': sample_volunteer_data['email'],
            'password': sample_volunteer_data['password']
        }
    })
    
    assert response.status_code == 200
    data = response.get_json()
    access_token = data['data']['access_token']
    
    return {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }


@pytest.fixture
def expired_registration_link(db_session, sample_camp, sample_user, sample_category):
    """Create an expired registration link for testing"""
    registration_link = RegistrationLink(
        name='Expired Link',
        allowed_categories=[str(sample_category.id)],
        is_active=True,
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),  # Expired
        usage_limit=100,
        usage_count=0,
        camp_id=sample_camp.id,
        created_by=sample_user.id
    )
    db.session.add(registration_link)
    db.session.commit()
    return registration_link


@pytest.fixture
def full_usage_registration_link(db_session, sample_camp, sample_user, sample_category):
    """Create a registration link that has reached usage limit"""
    registration_link = RegistrationLink(
        name='Full Usage Link',
        allowed_categories=[str(sample_category.id)],
        is_active=True,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        usage_limit=1,
        usage_count=1,  # At limit
        camp_id=sample_camp.id,
        created_by=sample_user.id
    )
    db.session.add(registration_link)
    db.session.commit()
    return registration_link


# Helper functions for tests
def create_test_user(db_session, email="test@example.com", role="camp_manager"):
    """Helper function to create a test user"""
    user = User(
        email=email,
        full_name="Test User",
        role=role
    )
    user.set_password("testpassword123")
    db.session.add(user)
    db.session.commit()
    return user


def create_test_camp(db_session, user, name="Test Camp"):
    """Helper function to create a test camp"""
    camp = Camp(
        name=name,
        start_date=datetime.now(timezone.utc).date() + timedelta(days=30),
        end_date=datetime.now(timezone.utc).date() + timedelta(days=35),
        location="Test Location",
        base_fee=Decimal('100.00'),
        capacity=100,
        description="Test camp description",
        registration_deadline=datetime.now(timezone.utc) + timedelta(days=20),
        camp_manager_id=user.id
    )
    db.session.add(camp)
    db.session.commit()
    return camp


def get_auth_token(client, email="test@example.com", password="testpassword123"):
    """Helper function to get authentication token"""
    response = client.post('/auth/login', json={
        'data': {
            'email': email,
            'password': password
        }
    })
    
    if response.status_code == 200:
        data = response.get_json()
        return data['data']['access_token']
    return None
