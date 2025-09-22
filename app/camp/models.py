from datetime import datetime, timezone
from sqlalchemy import Text, JSON, String, UniqueConstraint

from app.extensions import db
from app._shared.models import BaseModel

registration_payments = db.Table('registration_payments',
    db.Column('registration_id', String(36), db.ForeignKey('registrations.id'), primary_key=True),
    db.Column('payment_id', String(36), db.ForeignKey('payments.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
)


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
    region = db.Column(db.String(255), nullable=True)
    camp_id = db.Column(String(36), db.ForeignKey('camps.id'), nullable=False)
    
    # Relationships
    registrations = db.relationship('Registration', backref='church', lazy=True)

    __table_args__ = (
        UniqueConstraint('name', 'district', 'area', 'camp_id', name='church_name_district_area_camp_id_unique'),
    )

    def to_dict(self, for_api=False, include_registrations=True):
        if not include_registrations:
            return {
                'id': self.id,
                'name': self.name,
                'district': self.district,
                'area': self.area,
                'camp_id': self.camp_id,
                'region': self.region
            }
        return {
            'id': self.id,
            'name': self.name,
            'district': self.district,
            'area': self.area,
            'camp_id': self.camp_id,
            'region': self.region,
            'registrations': [registration.to_dict(for_api=for_api, include_payments=True) for registration in self.registrations]
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
    form_description = db.Column(db.Text, nullable=True, default=None)
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
            'form_description': self.form_description,
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
    sex = db.Column(db.Enum('male', 'female', 'other', name='sex'), nullable=False, default='other')
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
    otp_code = db.Column(db.String(6), nullable=True, default=None)
    otp_requested = db.Column(db.Boolean, default=False, nullable=False)
    
    # Relationships
    payments = db.relationship(
        'Payment',
        secondary=registration_payments,
        back_populates='registrations',
        lazy='dynamic'
    )
    
    # __table_args__ = (
    #     UniqueConstraint('email', 'phone_number', 'camp_id', name='registration_email_phone_camp_unique'),
    # )
    
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

    def get_total_payments(self):
        """Calculate total amount paid by this registration"""
        return sum(float(payment.amount) for payment in self.payments)
    
    def get_outstanding_balance(self):
        """Calculate outstanding balance for this registration"""
        return float(self.total_amount) - self.get_total_payments()
    
    def is_fully_paid(self):
        """Check if registration is fully paid"""
        return self.get_outstanding_balance() <= 0

    def to_dict(self, for_api=False, include_payments=False):
        result = {
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
            'sex': self.sex,
            'registration_link_id': self.registration_link_id,
            'registration_date': self.registration_date,
        }
        if include_payments:
            result['total_payments'] = self.get_total_payments()
            result['outstanding_balance'] = self.get_outstanding_balance()
            result['is_fully_paid'] = self.is_fully_paid()
            result['payments'] = [payment.to_dict(for_api=False) for payment in self.payments]
        return result


class Payment(BaseModel):
    """Payment model"""
    __tablename__ = 'payments'
    
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    payment_channel = db.Column(
        db.Enum('momo', 'cash', 'cheque', 'bank_transfer', 'card', name='payment_channel'), 
        nullable=False
    )
    recorded_by = db.Column(String(36), db.ForeignKey('users.id'), nullable=False)
    payment_reference = db.Column(db.String(100), nullable=True)
    payment_metadata = db.Column(JSON, nullable=True)
    camp_id = db.Column(String(36), db.ForeignKey('camps.id'), nullable=False)
    
    # Relationships
    registrations = db.relationship(
        'Registration',
        secondary=registration_payments,
        back_populates='payments',
        lazy='dynamic'
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.payment_date is None:
            self.payment_date = datetime.now(timezone.utc)
    
    def to_dict(self, for_api=True):
        result = {
            'id': self.id,
            'amount': float(self.amount) if self.amount else 0,
            'payment_date': self.payment_date,
            'payment_channel': self.payment_channel,
            'recorded_by': self.recorded_by,
            'payment_reference': self.payment_reference,
            'payment_metadata': self.payment_metadata,
        }
        
        if for_api:
            # Include registration details for API responses
            result['registrations'] = [
                {
                    'id': reg.id,
                    'camper_name': f"{reg.surname} {reg.last_name}",
                    'camp_id': reg.camp_id
                } 
                for reg in self.registrations
            ]
        
        return result
    
    def get_total_allocated_amount(self):
        """Get total amount allocated to registrations from this payment"""
        return sum(float(reg.total_amount) for reg in self.registrations)
    
    def get_remaining_amount(self):
        """Get remaining unallocated amount from this payment"""
        return float(self.amount) - self.get_total_allocated_amount()



class Financial(BaseModel):
    __tablename__ = 'financial_transactions'
    
    # Core financial fields
    amount = db.Column(db.Numeric(precision=10, scale=2), nullable=False)
    received_by = db.Column(db.String(100), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # 'income', 'expense'
    transaction_category = db.Column(db.String(50), nullable=False)  # 'offering', 'sales', etc.
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Additional important fields
    description = db.Column(db.Text)  # For detailed notes about the transaction
    reference_number = db.Column(db.String(50))  # For tracking/receipts
    payment_method = db.Column(db.String(20))  # 'cash', 'check', 'momo', 'bank_transfer'
    
    # Optional fields for better tracking
    approved_by = db.Column(db.String(100))  # Who approved this transaction
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    camp_id = db.Column(String(36), db.ForeignKey('camps.id'), nullable=False)


    __table_args__ = (
        UniqueConstraint("reference_number", "camp_id", name="uq_reference_camp"),
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.date is None:
            self.date = datetime.now(timezone.utc)

    
    def to_dict(self):
        return {
            'id': self.id,
            'amount': float(self.amount),
            'received_by': self.received_by,
            'transaction_type': self.transaction_type,
            'transaction_category': self.transaction_category,
            'date': self.date,
            'description': self.description,
            'reference_number': self.reference_number,
            'payment_method': self.payment_method,
            'approved_by': self.approved_by,
            'is_deleted': self.is_deleted,
            'camp_id': self.camp_id,
        }

class Inventory(BaseModel):
    __tablename__ = 'inventory'
    
    # Core inventory fields
    cost = db.Column(db.Numeric(precision=10, scale=2), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    inventory_type = db.Column(db.String(20), nullable=False)  # 'shirts', 'hoodies', 'wristbands', etc.
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    
    # Additional important fields for inventory management
    quantity = db.Column(db.Integer, nullable=False, default=0)
    camp_id = db.Column(String(36), db.ForeignKey('camps.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'cost': float(self.cost),
            'name': self.name,
            'description': self.description,
            'inventory_type': self.inventory_type,
            'is_deleted': self.is_deleted,
            'quantity': self.quantity,
            'camp_id': self.camp_id,
        }


class Purchase(BaseModel):
    __tablename__ = 'purchases'
    
    # Core purchase fields
    amount = db.Column(db.Numeric(precision=10, scale=2), nullable=False)
    purchase_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    camp_id = db.Column(String(36), db.ForeignKey('camps.id'), nullable=False)
    items = db.Column(JSON, nullable=False)  # Changed from inventory_ids to items with quantities
    sold_by = db.Column(String(36), db.ForeignKey('users.id'), nullable=False)
    
    # Keep inventory_ids for backward compatibility (will be deprecated)
    inventory_ids = db.Column(db.String(100), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'amount': float(self.amount),
            'purchase_date': self.purchase_date,
            'camp_id': self.camp_id,
            'items': self.items,
            'sold_by': self.sold_by,
            # Include legacy field for backward compatibility
            'inventory_ids': self.inventory_ids,
        }


class Pledge(BaseModel):
    __tablename__ = 'pledges'
    
    # Core pledge fields
    amount = db.Column(db.Numeric(precision=10, scale=2), nullable=False)
    pledge_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    camp_id = db.Column(String(36), db.ForeignKey('camps.id'), nullable=False)
    camper_id = db.Column(String(36), db.ForeignKey('registrations.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'amount': float(self.amount),
            'pledge_date': self.pledge_date,
            'camp_id': self.camp_id,
            'camper_id': self.camper_id,
            'status': self.status,
        }


class Room(BaseModel):
    __tablename__ = "rooms"

    hostel_name = db.Column(db.String(100), nullable=False)
    block = db.Column(db.String(50), nullable=True)
    room_number = db.Column(db.String(20), nullable=False)
    room_capacity = db.Column(db.Integer, default=1)
    is_special_room = db.Column(db.Boolean, default=False)
    extra_beds = db.Column(db.Integer, default=0)
    room_gender = db.Column(db.String(10), nullable=False)  # male, female, other
    is_damaged = db.Column(db.Boolean, default=False)
    misc_info = db.Column(db.Text, nullable=True)
    camp_id = db.Column(String(36), db.ForeignKey('camps.id'), nullable=False)
    adjoining_to = db.Column(String(36), nullable=True, default=None)

    # Relationships
    room_allocations = db.relationship('RoomAllocation', backref='room', lazy=True, cascade='all, delete-orphan')

    __table_args__ = (
        UniqueConstraint("hostel_name", "block", "room_number", "camp_id", name="uq_room_number_camp"),
    )

    def __repr__(self):
        return f"<Room {self.hostel_name} {self.block}-{self.room_number}>"

    def get_current_occupancy(self):
        """Get current number of campers allocated to this room"""
        return len([allocation for allocation in self.room_allocations if allocation.is_active])

    def get_available_capacity(self):
        """Get available capacity in this room"""
        total_capacity = self.room_capacity + self.extra_beds
        current_occupancy = self.get_current_occupancy()
        return max(0, total_capacity - current_occupancy)

    def is_full(self):
        """Check if room is at full capacity"""
        return self.get_available_capacity() == 0

    def to_dict(self, include_allocations=False):
        result = {
            "id": self.id,
            "hostel_name": self.hostel_name,
            "block": self.block,
            "room_number": self.room_number,
            "room_capacity": self.room_capacity,
            "is_special_room": self.is_special_room,
            "extra_beds": self.extra_beds,
            "room_gender": self.room_gender,
            "is_damaged": self.is_damaged,
            "misc_info": self.misc_info,
            "adjoining_to": self.adjoining_to,
            "camp_id": self.camp_id,
            "current_occupancy": self.get_current_occupancy(),
            "available_capacity": self.get_available_capacity(),
            "is_full": self.is_full()
        }
        
        if include_allocations:
            result["allocations"] = [allocation.to_dict() for allocation in self.room_allocations if allocation.is_active]
        
        return result


class RoomAllocation(BaseModel):
    __tablename__ = "room_allocations"

    room_id = db.Column(String(36), db.ForeignKey('rooms.id'), nullable=False)
    registration_id = db.Column(String(36), db.ForeignKey('registrations.id'), nullable=False)
    camp_id = db.Column(String(36), db.ForeignKey('camps.id'), nullable=False)
    allocated_by = db.Column(String(36), db.ForeignKey('users.id'), nullable=False)
    allocation_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    notes = db.Column(db.Text, nullable=True)

    # Relationships
    registration = db.relationship('Registration', backref='room_allocation', lazy=True)
    allocator = db.relationship('User', backref='room_allocations', lazy=True)

    __table_args__ = (
        UniqueConstraint("registration_id", "camp_id", "is_active", name="uq_registration_camp_allocation"),
    )

    def __repr__(self):
        return f"<RoomAllocation {self.registration_id} -> {self.room_id}>"

    def to_dict(self, include_details=False):
        result = {
            "id": self.id,
            "room_id": self.room_id,
            "registration_id": self.registration_id,
            "camp_id": self.camp_id,
            "allocated_by": self.allocated_by,
            "allocation_date": self.allocation_date,
            "is_active": self.is_active,
            "notes": self.notes
        }
        
        if include_details:
            result["room"] = self.room.to_dict() if self.room else None
            result["registration"] = self.registration.to_dict() if self.registration else None
            result["allocator_name"] = self.allocator.full_name if self.allocator else None
        
        return result


class Food(BaseModel):
    __tablename__ = 'foods'
    
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    vendor = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    category = db.Column(db.String(50), nullable=False) # Lunch, Supper, Snacks
    camp_id = db.Column(String(36), db.ForeignKey('camps.id'), nullable=False)
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "quantity": self.quantity,
            "vendor": self.vendor,
            "date": self.date,
            "category": self.category,
            "camp_id": self.camp_id,
        }


class FoodAllocation(BaseModel):
    __tablename__ = 'food_allocations'
    
    food_id = db.Column(String(36), db.ForeignKey('foods.id'), nullable=False)
    registration_id = db.Column(String(36), db.ForeignKey('registrations.id'), nullable=False)
    camp_id = db.Column(String(36), db.ForeignKey('camps.id'), nullable=False)
    allocated_by = db.Column(String(36), db.ForeignKey('users.id'), nullable=False)
    allocation_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "food_id": self.food_id,
            "registration_id": self.registration_id,
            "camp_id": self.camp_id,
            "allocated_by": self.allocated_by,
            "allocation_date": self.allocation_date,
        }


    