from datetime import datetime, timezone
from sqlalchemy import Text, JSON, String

from app.extensions import db
from app._shared.models import BaseModel


class Camp(BaseModel):
    """Camp model"""
    __tablename__ = 'camps'
    
    name = db.Column(db.String(255), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    location = db.Column(db.String(500), nullable=False)
    base_fee = db.Column(db.Numeric(10, 2), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    description = db.Column(Text)
    registration_deadline = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False, server_default='1')
        
    # Relationships
    churches = db.relationship('Church', backref='camp', lazy=True, cascade='all, delete-orphan')
    categories = db.relationship('Category', backref='camp', lazy=True, cascade='all, delete-orphan')
    custom_fields = db.relationship('CustomField', backref='camp', lazy=True, cascade='all, delete-orphan')
    registrations = db.relationship('Registration', backref='camp', lazy=True, cascade='all, delete-orphan')
    # expenses = db.relationship('Expense', backref='camp', lazy=True, cascade='all, delete-orphan')
    registration_links = db.relationship('RegistrationLink', backref='camp', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.is_active is None:
            self.is_active = True

    def to_dict(self, for_api=False):
        return {
            'id': self.id,
            'name': self.name,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'location': self.location,
            'base_fee': self.base_fee,
            'capacity': self.capacity,
            'description': self.description,
            'registration_deadline': self.registration_deadline,
            'is_active': self.is_active,
            'churches': [church.to_dict(for_api=for_api) for church in self.churches],
            'categories': [category.to_dict(for_api=for_api) for category in self.categories],
            'custom_fields': [custom_field.to_dict(for_api=for_api) for custom_field in self.custom_fields],
            'registrations': [registration.to_dict(for_api=for_api) for registration in self.registrations],
            'registration_links': [registration_link.to_dict(for_api=for_api) for registration_link in self.registration_links]
        }


class CampWorker(BaseModel):
    """Camp worker model"""
    __tablename__ = 'camp_workers'
    
    user_id = db.Column(String(36), db.ForeignKey('users.id'), nullable=False)
    camp_id = db.Column(String(36), db.ForeignKey('camps.id'), nullable=False)
    role = db.Column(db.Enum('camp_manager', 'volunteer', name='user_roles'), nullable=False)
    
    # Relationships
    user = db.relationship('User', backref='camp_workers', lazy=True)
    camp = db.relationship('Camp', backref='camp_workers', lazy=True)

    def to_dict(self, for_api=False):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'camp_id': self.camp_id,
            'role': self.role,
            'user': self.user.to_dict(for_api=for_api),
            'camp': self.camp.to_dict(for_api=for_api)
        }


class Church(BaseModel):
    """Church model"""
    __tablename__ = 'churches'
    
    name = db.Column(db.String(255), nullable=False)
    district = db.Column(db.String(255), nullable=True)
    area = db.Column(db.String(255), nullable=True)
    camp_id = db.Column(String(36), db.ForeignKey('camps.id'), nullable=False)
    
    # Relationships
    registrations = db.relationship('Registration', backref='church', lazy=True)

    __table_args__ = (
        db.UniqueConstraint('name', 'district', 'area', 'camp_id', name='church_name_district_area_camp_id_unique'),
    )

    def to_dict(self, for_api=False):
        return {
            'id': self.id,
            'name': self.name,
            'district': self.district,
            'area': self.area,
            'camp_id': self.camp_id,
            'registrations': [registration.to_dict(for_api=for_api) for registration in self.registrations]
        }


class Category(BaseModel):
    """Category model for registration types"""
    __tablename__ = 'categories'
    
    name = db.Column(db.String(255), nullable=False)
    discount_percentage = db.Column(db.Numeric(5, 2), default=0)
    discount_amount = db.Column(db.Numeric(10, 2), default=0)
    camp_id = db.Column(String(36), db.ForeignKey('camps.id'), nullable=False)
    is_default = db.Column(db.Boolean, default=False, nullable=False)
    
    # Relationships
    registrations = db.relationship('Registration', backref='category', lazy=True)

    def to_dict(self, for_api=False):
        return {
            'id': self.id,
            'name': self.name,
            'discount_percentage': self.discount_percentage,
            'discount_amount': self.discount_amount,
            'camp_id': self.camp_id,
            'is_default': self.is_default,
            'registrations': [registration.to_dict(for_api=for_api) for registration in self.registrations]
        }


class CustomField(BaseModel):
    """Custom field model for dynamic form fields"""
    __tablename__ = 'custom_fields'
    
    field_name = db.Column(db.String(255), nullable=False)
    field_type = db.Column(db.Enum('text', 'number', 'dropdown', 'checkbox', 'date', 
                                  name='field_types'), nullable=False)
    is_required = db.Column(db.Boolean, default=False, nullable=False)
    options = db.Column(JSON)  # For dropdown/checkbox options
    camp_id = db.Column(String(36), db.ForeignKey('camps.id'), nullable=False)
    order = db.Column(db.Integer, default=0, nullable=False)

    def to_dict(self, for_api=False):
        return {
            'id': self.id,
            'field_name': self.field_name,
            'field_type': self.field_type,
            'is_required': self.is_required,
            'options': self.options,
            'camp_id': self.camp_id,
            'order': self.order
        }

class RegistrationLink(BaseModel):
    """Registration link model for category-specific links"""
    __tablename__ = 'registration_links'
    
    camp_id = db.Column(String(36), db.ForeignKey('camps.id'), nullable=False)
    link_token = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    allowed_categories = db.Column(JSON)  # Array of category UUIDs
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    expires_at = db.Column(db.DateTime)
    usage_limit = db.Column(db.Integer)
    usage_count = db.Column(db.Integer, default=0, nullable=False)
    created_by = db.Column(String(36), db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    registrations = db.relationship('Registration', backref='registration_link', lazy=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.link_token:
            self.link_token = self.generate_token()
    
    def generate_token(self):
        """Generate unique token for registration link"""
        import secrets
        import string
        prefix = self.name.lower().replace(' ', '_')[:3] if self.name else 'reg'
        suffix = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(12))
        return f"{prefix}_{suffix}"
    
    def is_valid(self):
        """Check if registration link is valid"""
        if not self.is_active:
            return False
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at.replace(tzinfo=timezone.utc):
            return False
        if self.usage_limit and self.usage_count >= self.usage_limit:
            return False
        return True

    def to_dict(self, for_api=False):
        return {
            'id': self.id,
            'camp_id': self.camp_id,
            'link_token': self.link_token,
            'name': self.name,
            'allowed_categories': self.allowed_categories,
            'is_active': self.is_active,
            'expires_at': self.expires_at,
            'usage_limit': self.usage_limit,
            'usage_count': self.usage_count,
            'created_by': self.created_by,
            'registrations': [registration.to_dict(for_api=for_api) for registration in self.registrations]
        }


class Registration(BaseModel):
    """Registration model"""
    __tablename__ = 'registrations'
    
    surname = db.Column(db.String(255), nullable=False)
    middle_name = db.Column(db.String(255), default='')
    last_name = db.Column(db.String(255), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String(255))  # Optional
    phone_number = db.Column(db.String(20), nullable=False)
    emergency_contact_name = db.Column(db.String(255), nullable=False)
    emergency_contact_phone = db.Column(db.String(20), nullable=False)
    church_id = db.Column(String(36), db.ForeignKey('churches.id'), nullable=False)
    category_id = db.Column(String(36), db.ForeignKey('categories.id'), nullable=False)
    custom_field_responses = db.Column(JSON)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    has_paid = db.Column(db.Boolean, default=False, nullable=False)
    has_checked_in = db.Column(db.Boolean, default=False, nullable=False)
    camp_id = db.Column(String(36), db.ForeignKey('camps.id'), nullable=False, index=True)
    camper_code = db.Column(db.String(10), nullable=True, default=None)
    registration_link_id = db.Column(String(36), db.ForeignKey('registration_links.id'))
    registration_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    # payments = db.relationship('Payment', backref='registration', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.registration_date is None:
            self.registration_date = datetime.now(timezone.utc)
    
    def calculate_total_amount(self):
        """Calculate total amount based on base fee and category discount"""
        base_fee = float(self.camp.base_fee)
        category = self.category
        
        if category.discount_amount and category.discount_amount > 0:
            # Fixed amount discount
            return max(0, base_fee - float(category.discount_amount))
        elif category.discount_percentage and category.discount_percentage > 0:
            # Percentage discount
            discount = base_fee * (float(category.discount_percentage) / 100)
            return max(0, base_fee - discount)
        
        return base_fee

    def to_dict(self, for_api=False):
        return {
            'id': self.id,
            'surname': self.surname,
            'middle_name': self.middle_name,
            'last_name': self.last_name,
            'age': self.age,
            'email': self.email,
            'phone_number': self.phone_number,
            'emergency_contact_name': self.emergency_contact_name,
            'emergency_contact_phone': self.emergency_contact_phone,
            'church_id': self.church_id,
            'category_id': self.category_id,
            'custom_field_responses': self.custom_field_responses,
            'total_amount': self.total_amount,
            'has_paid': self.has_paid,
            'has_checked_in': self.has_checked_in,
            'camp_id': self.camp_id,
            'camper_code': self.camper_code,
            'registration_link_id': self.registration_link_id,
            'registration_date': self.registration_date,
            # 'payments': [payment.to_dict(for_api=for_api) for payment in self.payments]
        }
