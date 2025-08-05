"""
Unit tests for CampManager API models

This module contains tests for all database models including User, Camp,
Church, Category, CustomField, RegistrationLink, and Registration models.
"""

import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import uuid

from app.user.models import User
from app.camp.models import Camp, Church, Category, CustomField, RegistrationLink, Registration


@pytest.mark.unit
class TestBaseModel:
    """Test BaseModel functionality"""
    
    def test_base_model_fields(self, sample_user):
        """Test that BaseModel provides common fields"""
        assert hasattr(sample_user, 'id')
        assert hasattr(sample_user, 'created_at')
        assert hasattr(sample_user, 'updated_at')
        assert isinstance(sample_user.id, uuid.UUID)
        assert isinstance(sample_user.created_at, datetime)
        assert isinstance(sample_user.updated_at, datetime)
    
    def test_to_dict_method(self, sample_user):
        """Test BaseModel to_dict method"""
        user_dict = sample_user.to_dict()
        
        assert isinstance(user_dict, dict)
        assert 'id' in user_dict
        assert 'created_at' in user_dict
        assert 'updated_at' in user_dict
        assert 'email' in user_dict
        assert 'full_name' in user_dict
        assert 'role' in user_dict
        
        # Password hash should not be included
        assert 'password_hash' not in user_dict
        
        # Check that UUID and datetime are converted to strings
        assert isinstance(user_dict['id'], str)
        assert isinstance(user_dict['created_at'], str)
        assert isinstance(user_dict['updated_at'], str)
    
    def test_save_method(self, db_session):
        """Test BaseModel save method"""
        user = User(
            email='save_test@example.com',
            full_name='Save Test User',
            role='camp_manager'
        )
        user.set_password('testpassword')
        
        # Save should add to session and commit
        saved_user = user.save()
        
        assert saved_user == user
        assert user.id is not None
        
        # Verify user is in database
        found_user = db_session.query(User).filter_by(email='save_test@example.com').first()
        assert found_user is not None
        assert found_user.id == user.id
    
    def test_update_method(self, sample_user, db_session):
        """Test BaseModel update method"""
        original_updated_at = sample_user.updated_at
        
        # Update user
        updated_user = sample_user.update(full_name='Updated Name')
        
        assert updated_user == sample_user
        assert sample_user.full_name == 'Updated Name'
        assert sample_user.updated_at > original_updated_at
        
        # Verify update in database
        db_session.refresh(sample_user)
        assert sample_user.full_name == 'Updated Name'
    
    def test_delete_method(self, db_session):
        """Test BaseModel delete method"""
        user = User(
            email='delete_test@example.com',
            full_name='Delete Test User',
            role='camp_manager'
        )
        user.set_password('testpassword')
        user.save()
        
        user_id = user.id
        
        # Delete user
        user.delete()
        
        # Verify user is deleted from database
        found_user = db_session.query(User).filter_by(id=user_id).first()
        assert found_user is None


@pytest.mark.unit
class TestUserModel:
    """Test User model"""
    
    def test_user_creation(self, sample_user_data):
        """Test user creation with valid data"""
        user = User(
            email=sample_user_data['email'],
            full_name=sample_user_data['full_name'],
            role=sample_user_data['role']
        )
        
        assert user.email == sample_user_data['email']
        assert user.full_name == sample_user_data['full_name']
        assert user.role == sample_user_data['role']
        assert user.password_hash is None  # Not set yet
    
    def test_set_password(self, sample_user_data):
        """Test password hashing"""
        user = User(
            email=sample_user_data['email'],
            full_name=sample_user_data['full_name'],
            role=sample_user_data['role']
        )
        
        user.set_password(sample_user_data['password'])
        
        assert user.password_hash is not None
        assert user.password_hash != sample_user_data['password']  # Should be hashed
        assert len(user.password_hash) > 0
    
    def test_check_password(self, sample_user, sample_user_data):
        """Test password verification"""
        # Correct password
        assert sample_user.check_password(sample_user_data['password']) is True
        
        # Incorrect password
        assert sample_user.check_password('wrongpassword') is False
        assert sample_user.check_password('') is False
    
    def test_user_to_dict_excludes_password(self, sample_user):
        """Test that to_dict excludes password_hash"""
        user_dict = sample_user.to_dict()
        
        assert 'password_hash' not in user_dict
        assert 'email' in user_dict
        assert 'full_name' in user_dict
        assert 'role' in user_dict
    
    def test_user_relationships(self, sample_user, sample_camp):
        """Test user relationships"""
        # User should have camps relationship
        assert hasattr(sample_user, 'camps')
        assert sample_camp in sample_user.camps
        
        # User should have registration_links relationship
        assert hasattr(sample_user, 'registration_links')


@pytest.mark.unit
class TestCampModel:
    """Test Camp model"""
    
    def test_camp_creation(self, sample_camp_data, sample_user):
        """Test camp creation with valid data"""
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
        
        assert camp.name == sample_camp_data['name']
        assert camp.start_date == sample_camp_data['start_date']
        assert camp.end_date == sample_camp_data['end_date']
        assert camp.location == sample_camp_data['location']
        assert camp.base_fee == sample_camp_data['base_fee']
        assert camp.capacity == sample_camp_data['capacity']
        assert camp.description == sample_camp_data['description']
        assert camp.registration_deadline == sample_camp_data['registration_deadline']
        assert camp.camp_manager_id == sample_user.id
        assert camp.is_active is True  # Default value
    
    def test_camp_relationships(self, sample_camp, sample_church, sample_category):
        """Test camp relationships"""
        assert hasattr(sample_camp, 'churches')
        assert hasattr(sample_camp, 'categories')
        assert hasattr(sample_camp, 'custom_fields')
        assert hasattr(sample_camp, 'registrations')
        assert hasattr(sample_camp, 'registration_links')
        assert hasattr(sample_camp, 'manager')
        
        # Test actual relationships
        assert sample_church in sample_camp.churches
        assert sample_category in sample_camp.categories


@pytest.mark.unit
class TestChurchModel:
    """Test Church model"""
    
    def test_church_creation(self, sample_church_data, sample_camp):
        """Test church creation with valid data"""
        church = Church(
            name=sample_church_data['name'],
            camp_id=sample_camp.id
        )
        
        assert church.name == sample_church_data['name']
        assert church.camp_id == sample_camp.id
    
    def test_church_relationships(self, sample_church, sample_camp):
        """Test church relationships"""
        assert hasattr(sample_church, 'camp')
        assert hasattr(sample_church, 'registrations')
        assert sample_church.camp == sample_camp


@pytest.mark.unit
class TestCategoryModel:
    """Test Category model"""
    
    def test_category_creation(self, sample_category_data, sample_camp):
        """Test category creation with valid data"""
        category = Category(
            name=sample_category_data['name'],
            discount_percentage=sample_category_data['discount_percentage'],
            discount_amount=sample_category_data['discount_amount'],
            is_default=sample_category_data['is_default'],
            camp_id=sample_camp.id
        )
        
        assert category.name == sample_category_data['name']
        assert category.discount_percentage == sample_category_data['discount_percentage']
        assert category.discount_amount == sample_category_data['discount_amount']
        assert category.is_default == sample_category_data['is_default']
        assert category.camp_id == sample_camp.id
    
    def test_category_with_percentage_discount(self, sample_camp):
        """Test category with percentage discount"""
        category = Category(
            name='Student',
            discount_percentage=Decimal('20.00'),
            discount_amount=Decimal('0.00'),
            is_default=False,
            camp_id=sample_camp.id
        )
        
        assert category.discount_percentage == Decimal('20.00')
        assert category.discount_amount == Decimal('0.00')
    
    def test_category_with_amount_discount(self, sample_camp):
        """Test category with fixed amount discount"""
        category = Category(
            name='Early Bird',
            discount_percentage=Decimal('0.00'),
            discount_amount=Decimal('25.00'),
            is_default=False,
            camp_id=sample_camp.id
        )
        
        assert category.discount_percentage == Decimal('0.00')
        assert category.discount_amount == Decimal('25.00')
    
    def test_category_relationships(self, sample_category, sample_camp):
        """Test category relationships"""
        assert hasattr(sample_category, 'camp')
        assert hasattr(sample_category, 'registrations')
        assert sample_category.camp == sample_camp


@pytest.mark.unit
class TestCustomFieldModel:
    """Test CustomField model"""
    
    def test_custom_field_creation(self, sample_custom_field_data, sample_camp):
        """Test custom field creation with valid data"""
        custom_field = CustomField(
            field_name=sample_custom_field_data['field_name'],
            field_type=sample_custom_field_data['field_type'],
            is_required=sample_custom_field_data['is_required'],
            options=sample_custom_field_data['options'],
            order=sample_custom_field_data['order'],
            camp_id=sample_camp.id
        )
        
        assert custom_field.field_name == sample_custom_field_data['field_name']
        assert custom_field.field_type == sample_custom_field_data['field_type']
        assert custom_field.is_required == sample_custom_field_data['is_required']
        assert custom_field.options == sample_custom_field_data['options']
        assert custom_field.order == sample_custom_field_data['order']
        assert custom_field.camp_id == sample_camp.id
    
    def test_dropdown_custom_field(self, sample_camp):
        """Test dropdown custom field with options"""
        options = ['Small', 'Medium', 'Large', 'Extra Large']
        custom_field = CustomField(
            field_name='T-Shirt Size',
            field_type='dropdown',
            is_required=True,
            options=options,
            order=1,
            camp_id=sample_camp.id
        )
        
        assert custom_field.field_type == 'dropdown'
        assert custom_field.options == options
        assert custom_field.is_required is True
    
    def test_custom_field_relationships(self, sample_custom_field, sample_camp):
        """Test custom field relationships"""
        assert hasattr(sample_custom_field, 'camp')
        assert sample_custom_field.camp == sample_camp


@pytest.mark.unit
class TestRegistrationLinkModel:
    """Test RegistrationLink model"""
    
    def test_registration_link_creation(self, sample_registration_link_data, sample_camp, sample_user, sample_category):
        """Test registration link creation with valid data"""
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
        
        assert registration_link.name == sample_registration_link_data['name']
        assert registration_link.allowed_categories == [str(sample_category.id)]
        assert registration_link.is_active == sample_registration_link_data['is_active']
        assert registration_link.expires_at == sample_registration_link_data['expires_at']
        assert registration_link.usage_limit == sample_registration_link_data['usage_limit']
        assert registration_link.usage_count == sample_registration_link_data['usage_count']
        assert registration_link.camp_id == sample_camp.id
        assert registration_link.created_by == sample_user.id
    
    def test_registration_link_token_generation(self, sample_camp, sample_user, sample_category):
        """Test that registration link generates token automatically"""
        registration_link = RegistrationLink(
            name='Test Link',
            allowed_categories=[str(sample_category.id)],
            camp_id=sample_camp.id,
            created_by=sample_user.id
        )
        
        assert registration_link.link_token is not None
        assert len(registration_link.link_token) > 0
        assert '_' in registration_link.link_token  # Should have prefix_suffix format
    
    def test_registration_link_is_valid_active(self, sample_registration_link):
        """Test is_valid method for active link"""
        assert sample_registration_link.is_valid() is True
    
    def test_registration_link_is_valid_inactive(self, sample_registration_link):
        """Test is_valid method for inactive link"""
        sample_registration_link.is_active = False
        assert sample_registration_link.is_valid() is False
    
    def test_registration_link_is_valid_expired(self, expired_registration_link):
        """Test is_valid method for expired link"""
        assert expired_registration_link.is_valid() is False
    
    def test_registration_link_is_valid_usage_limit_reached(self, full_usage_registration_link):
        """Test is_valid method for link at usage limit"""
        assert full_usage_registration_link.is_valid() is False
    
    def test_registration_link_relationships(self, sample_registration_link, sample_camp, sample_user):
        """Test registration link relationships"""
        assert hasattr(sample_registration_link, 'camp')
        assert hasattr(sample_registration_link, 'manager')
        assert hasattr(sample_registration_link, 'registrations')
        assert sample_registration_link.camp == sample_camp
        assert sample_registration_link.manager == sample_user


@pytest.mark.unit
class TestRegistrationModel:
    """Test Registration model"""
    
    def test_registration_creation(self, sample_registration_data, sample_camp, sample_church, sample_category):
        """Test registration creation with valid data"""
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
        
        assert registration.surname == sample_registration_data['surname']
        assert registration.middle_name == sample_registration_data['middle_name']
        assert registration.last_name == sample_registration_data['last_name']
        assert registration.age == sample_registration_data['age']
        assert registration.email == sample_registration_data['email']
        assert registration.phone_number == sample_registration_data['phone_number']
        assert registration.emergency_contact_name == sample_registration_data['emergency_contact_name']
        assert registration.emergency_contact_phone == sample_registration_data['emergency_contact_phone']
        assert registration.custom_field_responses == sample_registration_data['custom_field_responses']
        assert registration.total_amount == Decimal('100.00')
        assert registration.has_paid == sample_registration_data['has_paid']
        assert registration.has_checked_in == sample_registration_data['has_checked_in']
        assert registration.camp_id == sample_camp.id
        assert registration.church_id == sample_church.id
        assert registration.category_id == sample_category.id
    
    def test_calculate_total_amount_no_discount(self, sample_camp, sample_church, sample_category):
        """Test total amount calculation with no discount"""
        registration = Registration(
            surname='John',
            last_name='Doe',
            age=25,
            phone_number='+1234567890',
            emergency_contact_name='Jane Doe',
            emergency_contact_phone='+0987654321',
            total_amount=Decimal('0.00'),  # Will be calculated
            camp_id=sample_camp.id,
            church_id=sample_church.id,
            category_id=sample_category.id
        )
        
        # Mock the relationships for calculation
        registration.camp = sample_camp
        registration.category = sample_category
        
        calculated_amount = registration.calculate_total_amount()
        assert calculated_amount == float(sample_camp.base_fee)
    
    def test_calculate_total_amount_percentage_discount(self, sample_camp, sample_church, sample_discount_category):
        """Test total amount calculation with percentage discount"""
        registration = Registration(
            surname='John',
            last_name='Doe',
            age=25,
            phone_number='+1234567890',
            emergency_contact_name='Jane Doe',
            emergency_contact_phone='+0987654321',
            total_amount=Decimal('0.00'),
            camp_id=sample_camp.id,
            church_id=sample_church.id,
            category_id=sample_discount_category.id
        )
        
        # Mock the relationships for calculation
        registration.camp = sample_camp
        registration.category = sample_discount_category
        
        calculated_amount = registration.calculate_total_amount()
        expected_amount = float(sample_camp.base_fee) * 0.8  # 20% discount
        assert calculated_amount == expected_amount
    
    def test_calculate_total_amount_fixed_discount(self, sample_camp, sample_church):
        """Test total amount calculation with fixed amount discount"""
        # Create category with fixed discount
        fixed_discount_category = Category(
            name='Early Bird',
            discount_percentage=Decimal('0.00'),
            discount_amount=Decimal('25.00'),
            is_default=False,
            camp_id=sample_camp.id
        )
        
        registration = Registration(
            surname='John',
            last_name='Doe',
            age=25,
            phone_number='+1234567890',
            emergency_contact_name='Jane Doe',
            emergency_contact_phone='+0987654321',
            total_amount=Decimal('0.00'),
            camp_id=sample_camp.id,
            church_id=sample_church.id,
            category_id=fixed_discount_category.id
        )
        
        # Mock the relationships for calculation
        registration.camp = sample_camp
        registration.category = fixed_discount_category
        
        calculated_amount = registration.calculate_total_amount()
        expected_amount = float(sample_camp.base_fee) - 25.00  # $25 discount
        assert calculated_amount == expected_amount
    
    def test_registration_relationships(self, sample_registration, sample_camp, sample_church, sample_category):
        """Test registration relationships"""
        assert hasattr(sample_registration, 'camp')
        assert hasattr(sample_registration, 'church')
        assert hasattr(sample_registration, 'category')
        assert hasattr(sample_registration, 'registration_link')
        
        assert sample_registration.camp == sample_camp
        assert sample_registration.church == sample_church
        assert sample_registration.category == sample_category
    
    def test_registration_date_default(self, sample_camp, sample_church, sample_category):
        """Test that registration_date has default value"""
        registration = Registration(
            surname='John',
            last_name='Doe',
            age=25,
            phone_number='+1234567890',
            emergency_contact_name='Jane Doe',
            emergency_contact_phone='+0987654321',
            total_amount=Decimal('100.00'),
            camp_id=sample_camp.id,
            church_id=sample_church.id,
            category_id=sample_category.id
        )
        
        assert registration.registration_date is not None
        assert isinstance(registration.registration_date, datetime)
        
        # Should be recent (within last minute)
        now = datetime.now(timezone.utc)
        time_diff = now - registration.registration_date.replace(tzinfo=timezone.utc)
        assert time_diff.total_seconds() < 60
