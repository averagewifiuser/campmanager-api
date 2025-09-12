from apiflask import Schema
from marshmallow import fields, validate, validates, ValidationError
from datetime import datetime, date
import re
from decimal import Decimal

from app._shared.schemas import BaseResponseSchema

# Camp Schemas
class CampCreateSchema(Schema):
    """Schema for creating a camp"""
    name = fields.String(required=True, validate=validate.Length(min=2, max=255))
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)
    location = fields.String(required=True, validate=validate.Length(min=2, max=500))
    base_fee = fields.Decimal(required=True, validate=validate.Range(min=0))
    capacity = fields.Integer(required=True, validate=validate.Range(min=1))
    description = fields.String(validate=validate.Length(max=1000))
    registration_deadline = fields.DateTime(required=True)
    
    # @validates('end_date')
    # def validate_end_date(self, value):
    #     if hasattr(self, 'start_date') and value <= self.start_date:
    #         raise ValidationError('End date must be after start date')
    
    # @validates('registration_deadline')
    # def validate_registration_deadline(self, value):
    #     if hasattr(self, 'start_date') and value.date() > self.start_date:
    #         raise ValidationError('Registration deadline must be before or on start date')


class CampUpdateSchema(Schema):
    """Schema for updating a camp"""
    name = fields.String(validate=validate.Length(min=2, max=255))
    start_date = fields.Date()
    end_date = fields.Date()
    location = fields.String(validate=validate.Length(min=2, max=500))
    base_fee = fields.Decimal(validate=validate.Range(min=0))
    capacity = fields.Integer(validate=validate.Range(min=1))
    description = fields.String(validate=validate.Length(max=1000))
    registration_deadline = fields.DateTime()
    is_active = fields.Boolean()


class CampResponseSchema(BaseResponseSchema):
    """Schema for camp response"""
    name = fields.String()
    start_date = fields.Date()
    end_date = fields.Date()
    location = fields.String()
    base_fee = fields.Decimal()
    capacity = fields.Integer()
    description = fields.String()
    registration_deadline = fields.DateTime()
    is_active = fields.Boolean()


class CampStatsSchema(Schema):
    """Schema for camp statistics"""
    camp_id = fields.String()
    total_registrations = fields.Integer()
    paid_registrations = fields.Integer()
    unpaid_registrations = fields.Integer()
    checked_in_count = fields.Integer()
    total_capacity = fields.Integer()
    capacity_percentage = fields.Float()
    total_revenue = fields.Decimal()


# Church Schemas
class ChurchCreateSchema(Schema):
    """Schema for creating a church"""
    name = fields.String(required=True, validate=validate.Length(min=2, max=255))
    district = fields.String(validate=validate.Length(min=2, max=255))
    area = fields.String(validate=validate.Length(min=2, max=255))


class ChurchUpdateSchema(Schema):
    """Schema for updating a church"""
    name = fields.String(validate=validate.Length(min=2, max=255))
    district = fields.String(validate=validate.Length(min=2, max=255))
    area = fields.String(validate=validate.Length(min=2, max=255))


class ChurchResponseSchema(BaseResponseSchema):
    """Schema for church response"""
    name = fields.String()
    district = fields.String()
    area = fields.String()
    camp_id = fields.String()


# Category Schemas
class CategoryCreateSchema(Schema):
    """Schema for creating a category"""
    name = fields.String(required=True, validate=validate.Length(min=2, max=255))
    discount_percentage = fields.Decimal(validate=validate.Range(min=0, max=100))
    discount_amount = fields.Decimal(validate=validate.Range(min=0))
    is_default = fields.Boolean()
    
    # @validates('discount_percentage')
    # def validate_discount_percentage(self, value):
    #     if hasattr(self, 'discount_amount') and self.discount_amount > 0 and value > 0:
    #         raise ValidationError('Cannot set both discount percentage and discount amount')


class CategoryUpdateSchema(Schema):
    """Schema for updating a category"""
    name = fields.String(validate=validate.Length(min=2, max=255))
    discount_percentage = fields.Decimal(validate=validate.Range(min=0, max=100))
    discount_amount = fields.Decimal(validate=validate.Range(min=0))
    is_default = fields.Boolean()


class CategoryResponseSchema(BaseResponseSchema):
    """Schema for category response"""
    name = fields.String()
    discount_percentage = fields.Decimal()
    discount_amount = fields.Decimal()
    camp_id = fields.String()
    is_default = fields.Boolean()


# Custom Field Schemas
class CustomFieldCreateSchema(Schema):
    """Schema for creating a custom field"""
    field_name = fields.String(required=True, validate=validate.Length(min=2, max=255))
    field_type = fields.String(required=True, 
                              validate=validate.OneOf(['text', 'number', 'dropdown', 'checkbox', 'date']))
    is_required = fields.Boolean()
    options = fields.List(fields.String(), validate=validate.Length(min=1), allow_none=True)
    order = fields.Integer(validate=validate.Range(min=0))
    
    # @validates('options')
    # def validate_options(self, value):
    #     if hasattr(self, 'field_type') and self.field_type in ['dropdown', 'checkbox']:
    #         if not value or len(value) == 0:
    #             raise ValidationError('Options are required for dropdown and checkbox fields')


class CustomFieldUpdateSchema(Schema):
    """Schema for updating a custom field"""
    field_name = fields.String(validate=validate.Length(min=2, max=255))
    field_type = fields.String(validate=validate.OneOf(['text', 'number', 'dropdown', 'checkbox', 'date']))
    is_required = fields.Boolean()
    options = fields.List(fields.String(), allow_none=True)
    order = fields.Integer(validate=validate.Range(min=0))


class CustomFieldResponseSchema(BaseResponseSchema):
    """Schema for custom field response"""
    field_name = fields.String()
    field_type = fields.String()
    is_required = fields.Boolean()
    options = fields.List(fields.String(), allow_none=True)
    camp_id = fields.String()
    order = fields.Integer()


# Registration Link Schemas
class RegistrationLinkCreateSchema(Schema):
    """Schema for creating a registration link"""
    name = fields.String(required=True, validate=validate.Length(min=2, max=255))
    allowed_categories = fields.List(fields.String(), required=True, validate=validate.Length(min=1))
    expires_at = fields.DateTime(allow_none=True)
    usage_limit = fields.Integer(validate=validate.Range(min=1), allow_none=True)
    form_description = fields.String(allow_none=True)
    
    # @validates('expires_at')
    # def validate_expires_at(self, value):
    #     if value and value <= datetime.now():
    #         raise ValidationError('Expiration date must be in the future')


class RegistrationLinkUpdateSchema(Schema):
    """Schema for updating a registration link"""
    name = fields.String(validate=validate.Length(min=2, max=255))
    allowed_categories = fields.List(fields.String(), validate=validate.Length(min=1))
    expires_at = fields.DateTime(allow_none=True)
    usage_limit = fields.Integer(validate=validate.Range(min=1), allow_none=True)
    is_active = fields.Boolean()
    form_description = fields.String(allow_none=True)


class RegistrationLinkResponseSchema(BaseResponseSchema):
    """Schema for registration link response"""
    camp_id = fields.String()
    link_token = fields.String()
    name = fields.String()
    allowed_categories = fields.List(fields.String())
    is_active = fields.Boolean()
    expires_at = fields.DateTime(allow_none=True)
    usage_limit = fields.Integer(allow_none=True)
    usage_count = fields.Integer()
    created_by = fields.String()
    registration_url = fields.Method('get_registration_url')
    form_description = fields.String(allow_none=True)
    
    def get_registration_url(self, obj):
        # You'll need to configure this base URL
        return f"https://campmanager.com/register/{obj.link_token}"


# Registration Schemas
class RegistrationCreateSchema(Schema):
    """Schema for creating a registration"""
    surname = fields.String(required=True, validate=validate.Length(min=1, max=255))
    middle_name = fields.String(validate=validate.Length(max=255))
    last_name = fields.String(required=True, validate=validate.Length(min=1, max=255))
    age = fields.Integer(required=True, validate=validate.Range(min=1, max=150))
    sex = fields.String(required=True, validate=validate.OneOf(['male', 'female', 'other']))
    email = fields.Email(allow_none=True)
    phone_number = fields.String(required=True)
    emergency_contact_name = fields.String(required=True, validate=validate.Length(min=2, max=255))
    emergency_contact_phone = fields.String(required=True)
    church_id = fields.String(required=True)
    category_id = fields.String(required=True)
    custom_field_responses = fields.Dict(keys=fields.String(), values=fields.Raw())
    
    # @validates('phone_number')
    # def validate_phone_number(self, value):
    #     # Basic phone number validation (can be enhanced)
    #     if not re.match(r'^\+?[\d\s\-\(\)]{10,}$', value):
    #         raise ValidationError('Invalid phone number format')
    
    # @validates('emergency_contact_phone')
    # def validate_emergency_contact_phone(self, value):
    #     if not re.match(r'^\+?[\d\s\-\(\)]{10,}$', value):
    #         raise ValidationError('Invalid emergency contact phone number format')


class RegistrationUpdateSchema(Schema):
    """Schema for updating a registration"""
    surname = fields.String(validate=validate.Length(min=1, max=255))
    middle_name = fields.String(validate=validate.Length(max=255))
    last_name = fields.String(validate=validate.Length(min=1, max=255))
    age = fields.Integer(validate=validate.Range(min=1, max=150))
    sex = fields.String(validate=validate.OneOf(['male', 'female', 'other']))
    email = fields.Email(allow_none=True)
    phone_number = fields.String()
    emergency_contact_name = fields.String(validate=validate.Length(min=2, max=255))
    emergency_contact_phone = fields.String()
    church_id = fields.String()
    category_id = fields.String()
    custom_field_responses = fields.Dict(keys=fields.String(), values=fields.Raw())
    has_paid = fields.Boolean()
    has_checked_in = fields.Boolean()


class RegistrationResponseSchema(BaseResponseSchema):
    """Schema for registration response"""
    surname = fields.String()
    middle_name = fields.String()
    last_name = fields.String()
    age = fields.Integer()
    email = fields.String(allow_none=True)
    phone_number = fields.String()
    emergency_contact_name = fields.String()
    emergency_contact_phone = fields.String()
    church_id = fields.String()
    category_id = fields.String()
    custom_field_responses = fields.Dict()
    total_amount = fields.Decimal()
    has_paid = fields.Boolean()
    has_checked_in = fields.Boolean()
    camp_id = fields.String()
    registration_link_id = fields.String(allow_none=True)
    registration_date = fields.DateTime()
    camper_code = fields.String()
    
    # Nested objects for convenience
    church = fields.Nested(ChurchResponseSchema, dump_only=True)
    category = fields.Nested(CategoryResponseSchema, dump_only=True)


# Registration Form Schemas (for public endpoints)
class RegistrationFormSchema(Schema):
    """Schema for registration form data"""
    camp = fields.Nested(CampResponseSchema)
    churches = fields.List(fields.Nested(ChurchResponseSchema))
    categories = fields.List(fields.Nested(CategoryResponseSchema))
    custom_fields = fields.List(fields.Nested(CustomFieldResponseSchema))
    link_type = fields.String()  # 'general' or 'category_specific'
    registration_link = fields.Nested(RegistrationLinkResponseSchema, allow_none=True)



class CampCreateRequestSchema(Schema):
    """Wrapper for camp creation request"""
    data = fields.Nested(CampCreateSchema, required=True)


class CampUpdateRequestSchema(Schema):
    """Wrapper for camp update request"""
    data = fields.Nested(CampUpdateSchema, required=True)


class ChurchCreateRequestSchema(Schema):
    """Wrapper for church creation request"""
    data = fields.Nested(ChurchCreateSchema, required=True)


class ChurchUpdateRequestSchema(Schema):
    """Wrapper for church update request"""
    data = fields.Nested(ChurchUpdateSchema, required=True)


class CategoryCreateRequestSchema(Schema):
    """Wrapper for category creation request"""
    data = fields.Nested(CategoryCreateSchema, required=True)


class CategoryUpdateRequestSchema(Schema):
    """Wrapper for category update request"""
    data = fields.Nested(CategoryUpdateSchema, required=True)


class CustomFieldCreateRequestSchema(Schema):
    """Wrapper for custom field creation request"""
    data = fields.Nested(CustomFieldCreateSchema, required=True)


class CustomFieldUpdateRequestSchema(Schema):
    """Wrapper for custom field update request"""
    data = fields.Nested(CustomFieldUpdateSchema, required=True)


class RegistrationLinkCreateRequestSchema(Schema):
    """Wrapper for registration link creation request"""
    data = fields.Nested(RegistrationLinkCreateSchema, required=True)


class RegistrationLinkUpdateRequestSchema(Schema):
    """Wrapper for registration link update request"""
    data = fields.Nested(RegistrationLinkUpdateSchema, required=True)


class RegistrationCreateRequestSchema(Schema):
    """Wrapper for registration creation request"""
    data = fields.Nested(RegistrationCreateSchema, required=True)


class RegistrationUpdateRequestSchema(Schema):
    """Wrapper for registration update request"""
    data = fields.Nested(RegistrationUpdateSchema, required=True)




from apiflask import Schema
from marshmallow import fields, validate, validates, ValidationError, post_load
from datetime import datetime, date
import re


# Base Schemas
class BaseResponseSchema(Schema):
    """Base response schema with common fields"""
    id = fields.String(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


# User Schemas
class UserRegistrationSchema(Schema):
    """Schema for user registration"""
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate.Length(min=8))
    full_name = fields.String(required=True, validate=validate.Length(min=2))
    role = fields.String(validate=validate.OneOf(['camp_manager', 'volunteer']))


class UserLoginSchema(Schema):
    """Schema for user login"""
    email = fields.Email(required=True)
    password = fields.String(required=True)


class UserResponseSchema(BaseResponseSchema):
    """Schema for user response"""
    email = fields.Email()
    full_name = fields.String()
    role = fields.String()


# Camp Schemas
class CampCreateSchema(Schema):
    """Schema for creating a camp"""
    name = fields.String(required=True, validate=validate.Length(min=2, max=255))
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)
    location = fields.String(required=True, validate=validate.Length(min=2, max=500))
    base_fee = fields.Decimal(required=True, validate=validate.Range(min=0))
    capacity = fields.Integer(required=True, validate=validate.Range(min=1))
    description = fields.String(validate=validate.Length(max=1000))
    registration_deadline = fields.DateTime(required=True)
    
    # @validates('end_date')
    # def validate_end_date(self, value):
    #     if hasattr(self, 'start_date') and value <= self.start_date:
    #         raise ValidationError('End date must be after start date')
    
    # @validates('registration_deadline')
    # def validate_registration_deadline(self, value):
    #     if hasattr(self, 'start_date') and value.date() > self.start_date:
    #         raise ValidationError('Registration deadline must be before or on start date')


class CampUpdateSchema(Schema):
    """Schema for updating a camp"""
    name = fields.String(validate=validate.Length(min=2, max=255))
    start_date = fields.Date()
    end_date = fields.Date()
    location = fields.String(validate=validate.Length(min=2, max=500))
    base_fee = fields.Decimal(validate=validate.Range(min=0))
    capacity = fields.Integer(validate=validate.Range(min=1))
    description = fields.String(validate=validate.Length(max=1000))
    registration_deadline = fields.DateTime()
    is_active = fields.Boolean()


class CampResponseSchema(BaseResponseSchema):
    """Schema for camp response"""
    name = fields.String()
    start_date = fields.Date()
    end_date = fields.Date()
    location = fields.String()
    base_fee = fields.Decimal()
    capacity = fields.Integer()
    description = fields.String()
    registration_deadline = fields.DateTime()
    is_active = fields.Boolean()


class CampStatsSchema(Schema):
    """Schema for camp statistics"""
    camp_id = fields.String()
    total_registrations = fields.Integer()
    paid_registrations = fields.Integer()
    unpaid_registrations = fields.Integer()
    checked_in_count = fields.Integer()
    total_capacity = fields.Integer()
    capacity_percentage = fields.Float()
    total_revenue = fields.Decimal()


# Church Schemas
class ChurchCreateSchema(Schema):
    """Schema for creating a church"""
    name = fields.String(required=True, validate=validate.Length(min=2, max=255))
    district = fields.String(validate=validate.Length(min=2, max=255))
    area = fields.String(validate=validate.Length(min=2, max=255))


class ChurchUpdateSchema(Schema):
    """Schema for updating a church"""
    name = fields.String(validate=validate.Length(min=2, max=255))
    district = fields.String(validate=validate.Length(min=2, max=255))
    area = fields.String(validate=validate.Length(min=2, max=255))


class ChurchResponseSchema(BaseResponseSchema):
    """Schema for church response"""
    name = fields.String()
    district = fields.String()
    area = fields.String()
    camp_id = fields.String()


# Category Schemas
class CategoryCreateSchema(Schema):
    """Schema for creating a category"""
    name = fields.String(required=True, validate=validate.Length(min=2, max=255))
    discount_percentage = fields.Decimal(validate=validate.Range(min=0, max=100))
    discount_amount = fields.Decimal(validate=validate.Range(min=0))
    is_default = fields.Boolean()
    
    # @validates('discount_percentage')
    # def validate_discount_percentage(self, value):
    #     if hasattr(self, 'discount_amount') and self.discount_amount > 0 and value > 0:
    #         raise ValidationError('Cannot set both discount percentage and discount amount')


class CategoryUpdateSchema(Schema):
    """Schema for updating a category"""
    name = fields.String(validate=validate.Length(min=2, max=255))
    discount_percentage = fields.Decimal(validate=validate.Range(min=0, max=100))
    discount_amount = fields.Decimal(validate=validate.Range(min=0))
    is_default = fields.Boolean()


class CategoryResponseSchema(BaseResponseSchema):
    """Schema for category response"""
    name = fields.String()
    discount_percentage = fields.Decimal()
    discount_amount = fields.Decimal()
    camp_id = fields.String()
    is_default = fields.Boolean()


# Custom Field Schemas
class CustomFieldCreateSchema(Schema):
    """Schema for creating a custom field"""
    field_name = fields.String(required=True, validate=validate.Length(min=2, max=255))
    field_type = fields.String(required=True, 
                              validate=validate.OneOf(['text', 'number', 'dropdown', 'checkbox', 'date']))
    is_required = fields.Boolean()
    options = fields.List(fields.String(), validate=validate.Length(min=1), allow_none=True)
    order = fields.Integer(validate=validate.Range(min=0))
    
    # @validates('options')
    # def validate_options(self, value):
    #     if hasattr(self, 'field_type') and self.field_type in ['dropdown', 'checkbox']:
    #         if not value or len(value) == 0:
    #             raise ValidationError('Options are required for dropdown and checkbox fields')


class CustomFieldUpdateSchema(Schema):
    """Schema for updating a custom field"""
    field_name = fields.String(validate=validate.Length(min=2, max=255))
    field_type = fields.String(validate=validate.OneOf(['text', 'number', 'dropdown', 'checkbox', 'date']))
    is_required = fields.Boolean()
    options = fields.List(fields.String(), allow_none=True)
    order = fields.Integer(validate=validate.Range(min=0))


class CustomFieldResponseSchema(BaseResponseSchema):
    """Schema for custom field response"""
    field_name = fields.String()
    field_type = fields.String()
    is_required = fields.Boolean()
    options = fields.List(fields.String(), allow_none=True)
    camp_id = fields.String()
    order = fields.Integer()


# Registration Link Schemas
class RegistrationLinkCreateSchema(Schema):
    """Schema for creating a registration link"""
    name = fields.String(required=True, validate=validate.Length(min=2, max=255))
    allowed_categories = fields.List(fields.String(), required=True, validate=validate.Length(min=1))
    expires_at = fields.DateTime(allow_none=True)
    usage_limit = fields.Integer(validate=validate.Range(min=1), allow_none=True)
    form_description = fields.String(allow_none=True)
    
    
    # @validates('expires_at')
    # def validate_expires_at(self, value):
    #     if value and value <= datetime.now():
    #         raise ValidationError('Expiration date must be in the future')


class RegistrationLinkUpdateSchema(Schema):
    """Schema for updating a registration link"""
    name = fields.String(validate=validate.Length(min=2, max=255))
    allowed_categories = fields.List(fields.String(), validate=validate.Length(min=1))
    expires_at = fields.DateTime(allow_none=True)
    usage_limit = fields.Integer(validate=validate.Range(min=1), allow_none=True)
    is_active = fields.Boolean()
    form_description = fields.String(allow_none=True)


class RegistrationLinkResponseSchema(BaseResponseSchema):
    """Schema for registration link response"""
    camp_id = fields.String()
    link_token = fields.String()
    name = fields.String()
    allowed_categories = fields.List(fields.String())
    is_active = fields.Boolean()
    expires_at = fields.DateTime(allow_none=True)
    usage_limit = fields.Integer(allow_none=True)
    usage_count = fields.Integer()
    created_by = fields.String()
    registration_url = fields.Method('get_registration_url')
    form_description = fields.String(allow_none=True)
    
    def get_registration_url(self, obj):
        # You'll need to configure this base URL
        return f"https://localhost:5173/register/{obj['link_token']}"


# Registration Schemas
class RegistrationCreateSchema(Schema):
    """Schema for creating a registration"""
    surname = fields.String(required=True, validate=validate.Length(min=1, max=255))
    middle_name = fields.String(validate=validate.Length(max=255))
    last_name = fields.String(required=True, validate=validate.Length(min=1, max=255))
    age = fields.Integer(required=True, validate=validate.Range(min=1, max=150))
    sex = fields.String(required=True, validate=validate.OneOf(['male', 'female', 'other']))
    email = fields.Email(allow_none=True)
    phone_number = fields.String(required=True)
    emergency_contact_name = fields.String(required=True, validate=validate.Length(min=2, max=255))
    emergency_contact_phone = fields.String(required=True)
    church_id = fields.String(required=True)
    category_id = fields.String(required=True)
    custom_field_responses = fields.Dict(keys=fields.String(), values=fields.Raw())
    
    # @validates('phone_number')
    # def validate_phone_number(self, value):
    #     # Basic phone number validation (can be enhanced)
    #     if not re.match(r'^\+?[\d\s\-\(\)]{10,}$', value):
    #         raise ValidationError('Invalid phone number format')
    
    # @validates('emergency_contact_phone')
    # def validate_emergency_contact_phone(self, value):
    #     if not re.match(r'^\+?[\d\s\-\(\)]{10,}$', value):
    #         raise ValidationError('Invalid emergency contact phone number format')


class RegistrationUpdateSchema(Schema):
    """Schema for updating a registration"""
    surname = fields.String(validate=validate.Length(min=1, max=255))
    middle_name = fields.String(validate=validate.Length(max=255))
    last_name = fields.String(validate=validate.Length(min=1, max=255))
    age = fields.Integer(validate=validate.Range(min=1, max=150))
    sex = fields.String(validate=validate.OneOf(['male', 'female', 'other']))
    email = fields.Email(allow_none=True)
    phone_number = fields.String()
    emergency_contact_name = fields.String(validate=validate.Length(min=2, max=255))
    emergency_contact_phone = fields.String()
    church_id = fields.String()
    category_id = fields.String()
    custom_field_responses = fields.Dict(keys=fields.String(), values=fields.Raw())
    has_paid = fields.Boolean()
    has_checked_in = fields.Boolean()


class RegistrationResponseSchema(BaseResponseSchema):
    """Schema for registration response"""
    surname = fields.String()
    middle_name = fields.String()
    last_name = fields.String()
    age = fields.Integer()
    sex = fields.String()
    email = fields.String(allow_none=True)
    phone_number = fields.String()
    emergency_contact_name = fields.String()
    emergency_contact_phone = fields.String()
    church_id = fields.String()
    category_id = fields.String()
    custom_field_responses = fields.Dict()
    total_amount = fields.Decimal()
    has_paid = fields.Boolean()
    has_checked_in = fields.Boolean()
    camp_id = fields.String()
    registration_link_id = fields.String(allow_none=True)
    registration_date = fields.DateTime()
    camper_code = fields.String()
    total_payments = fields.Decimal(required=False)
    outstanding_balance = fields.Decimal(required=False)
    is_fully_paid = fields.Boolean(required=False)
    payments = fields.List(fields.Dict(), required=False)
    
    # Nested objects for convenience
    church = fields.Nested(ChurchResponseSchema, dump_only=True)
    category = fields.Nested(CategoryResponseSchema, dump_only=True)


# Registration Form Schemas (for public endpoints)
class RegistrationFormSchema(Schema):
    """Schema for registration form data"""
    camp = fields.Nested(CampResponseSchema)
    churches = fields.List(fields.Nested(ChurchResponseSchema))
    categories = fields.List(fields.Nested(CategoryResponseSchema))
    custom_fields = fields.List(fields.Nested(CustomFieldResponseSchema))
    link_type = fields.String()  # 'general' or 'category_specific'
    registration_link = fields.Nested(RegistrationLinkResponseSchema, allow_none=True)



# Payment Form Schemas
class PaymentFormSchema(Schema):
    """Schema for payment form data"""
    amount = fields.Decimal(required=True)
    payment_channel = fields.String(required=True, validate=validate.OneOf(['momo', 'cash', 'cheque', 'bank_transfer', 'card']))
    # payment_reference = fields.String()
    payment_metadata = fields.Dict()
    registration_ids = fields.List(fields.String(), required=True)


class PaymentFormRequestWrapperSchema(Schema):
    """Wrapper for payment form request"""
    data = fields.Nested(PaymentFormSchema, required=True)


class PaymentResponseSchema(BaseResponseSchema):
    amount = fields.Decimal(required=True)
    payment_channel = fields.String(required=True)
    payment_reference = fields.String()
    payment_metadata = fields.Dict()
    registrations = fields.List(fields.Dict())
    payment_date = fields.DateTime()
    recorded_by = fields.String()


class FinancialResponseSchema(BaseResponseSchema):
    amount = fields.Decimal(required=True)
    received_by = fields.String(required=True)
    transaction_type = fields.String(required=True)
    transaction_category = fields.String(required=True)
    date = fields.DateTime(required=True)
    description = fields.String(required=True)
    reference_number = fields.String(required=True)
    payment_method = fields.String(required=True)
    approved_by = fields.String()


class FinancialRequestSchema(Schema):
    """Wrapper for financial request"""
    amount = fields.Decimal(required=True)
    received_by = fields.String(required=True)
    transaction_type = fields.String(required=True, validate=validate.OneOf(['income', 'expense']))
    transaction_category = fields.String(required=True, validate=validate.OneOf(['offering', 'sales', 'donation', 'camp_payment', 'camp_expense', 'other', 'pledge']))
    date = fields.DateTime(required=True)
    description = fields.String(required=True)
    reference_number = fields.String(required=True)
    payment_method = fields.String(required=True, validate=validate.OneOf(['cash', 'check', 'momo', 'bank_transfer', 'card']))
    approved_by = fields.String()


class InventoryRequestSchema(Schema):
    cost = fields.Decimal(required=True)
    name = fields.String(required=True)
    description = fields.String()
    inventory_type = fields.String(required=True, validate=validate.OneOf([ 'shirts', 'hoodies',  'wristbands', 'sweat-shirts', 'keychain', 'caps', 'other']))
    quantity = fields.Integer(required=True)


class InventoryRequestWrapperSchema(Schema):
    data = fields.Nested(InventoryRequestSchema, required=True)

class InventoryResponseSchema(BaseResponseSchema):
    cost = fields.Decimal(required=True)
    name = fields.String(required=True)
    description = fields.String()
    inventory_type = fields.String(required=True, validate=validate.OneOf(['shirts', 'hoodies', 'wristbands', 'sweat-shirts', 'keychain', 'caps', 'other']))
    is_deleted = fields.Boolean(required=True)
    quantity = fields.Integer(required=True)
    camp_id = fields.String(required=True)


class InventoryResponseWrapperSchema(Schema):
    """Wrapper for inventory response"""
    data = fields.Nested(InventoryResponseSchema, required=True)


class InventoryListResponseWrapperSchema(Schema):
    """Wrapper for inventory list response"""
    data = fields.List(fields.Nested(InventoryResponseSchema), required=True)


# Purchase Schemas
class PurchaseItemSchema(Schema):
    """Schema for individual purchase item"""
    inventory_id = fields.String(required=True)
    quantity = fields.Integer(required=True, validate=validate.Range(min=1))

class PurchaseRequestSchema(Schema):
    """Schema for purchase request"""
    amount = fields.Decimal(required=True, validate=validate.Range(min=0))
    items = fields.List(fields.Nested(PurchaseItemSchema), required=True, validate=validate.Length(min=1))
    # Keep inventory_ids for backward compatibility
    inventory_ids = fields.String(required=False)


class PurchaseRequestWrapperSchema(Schema):
    """Wrapper for purchase request"""
    data = fields.Nested(PurchaseRequestSchema, required=True)


class PurchaseResponseSchema(BaseResponseSchema):
    """Schema for purchase response"""
    amount = fields.Decimal(required=True)
    purchase_date = fields.DateTime(required=True)
    camp_id = fields.String(required=True)
    items = fields.List(fields.Nested(PurchaseItemSchema), required=False)
    inventory_ids = fields.String(required=True)  # Keep for backward compatibility
    sold_by = fields.String(required=True)


class PurchaseResponseWrapperSchema(Schema):
    """Wrapper for purchase response"""
    data = fields.Nested(PurchaseResponseSchema, required=True)


class PurchaseListResponseWrapperSchema(Schema):
    """Wrapper for purchase list response"""
    data = fields.List(fields.Nested(PurchaseResponseSchema), required=True)


# Pledge Schemas
class PledgeRequestSchema(Schema):
    """Schema for pledge request"""
    amount = fields.Decimal(required=True, validate=validate.Range(min=0))
    camper_id = fields.String(required=True)
    status = fields.String(required=True, validate=validate.OneOf(['pending', 'fulfilled', 'cancelled']))


class PledgeStatusChangeSchema(Schema):
    """Schema for pledge status change request"""
    status = fields.String(required=True, validate=validate.OneOf(['pending', 'fulfilled', 'cancelled']))
    camp_id = fields.String(required=False)


class PledgeRequestWrapperSchema(Schema):
    """Wrapper for pledge request"""
    data = fields.Nested(PledgeRequestSchema, required=True)


class PledgeStatusChangeWrapperSchema(Schema):
    """Wrapper for pledge status change request"""
    data = fields.Nested(PledgeStatusChangeSchema, required=True)


class PledgeResponseSchema(BaseResponseSchema):
    """Schema for pledge response"""
    amount = fields.Decimal(required=True)
    pledge_date = fields.DateTime(required=True)
    camp_id = fields.String(required=True)
    camper_id = fields.String(required=True)
    camper_name = fields.String(required=True)
    camper_code = fields.String(required=True)
    status = fields.String(required=True)


class PledgeResponseWrapperSchema(Schema):
    """Wrapper for pledge response"""
    data = fields.Nested(PledgeResponseSchema, required=True)


class PledgeListResponseWrapperSchema(Schema):
    """Wrapper for pledge list response"""
    data = fields.List(fields.Nested(PledgeResponseSchema), required=True)


# Food Schemas
class FoodCreateSchema(Schema):
    """Schema for creating food"""
    name = fields.String(required=True, validate=validate.Length(min=2, max=100))
    quantity = fields.Integer(required=True, validate=validate.Range(min=1))
    vendor = fields.String(required=True, validate=validate.Length(min=2, max=100))
    date = fields.DateTime(required=True)
    category = fields.String(required=True, validate=validate.OneOf(['lunch', 'supper', 'snacks', 'breakfast']))


class FoodUpdateSchema(Schema):
    """Schema for updating food"""
    name = fields.String(validate=validate.Length(min=2, max=100))
    quantity = fields.Integer(validate=validate.Range(min=0))
    vendor = fields.String(validate=validate.Length(min=2, max=100))
    date = fields.DateTime()
    category = fields.String(validate=validate.OneOf(['lunch', 'supper', 'snacks', 'breakfast']))


class FoodResponseSchema(BaseResponseSchema):
    """Schema for food response"""
    name = fields.String()
    quantity = fields.Integer()
    vendor = fields.String()
    date = fields.DateTime()
    category = fields.String()
    camp_id = fields.String()
    allocated_quantity = fields.Integer(required=False)
    available_quantity = fields.Integer(required=False)


# Food Allocation Schemas
class FoodAllocationCreateSchema(Schema):
    """Schema for creating food allocation"""
    food_id = fields.String(required=True)
    registration_id = fields.String(required=True)


class FoodAllocationResponseSchema(BaseResponseSchema):
    """Schema for food allocation response"""
    food_id = fields.String()
    registration_id = fields.String()
    camp_id = fields.String()
    allocated_by = fields.String()
    allocation_date = fields.DateTime()
    food = fields.Nested(FoodResponseSchema, required=False)
    registration = fields.Nested(RegistrationResponseSchema, required=False)


class BulkFoodAllocationSchema(Schema):
    """Schema for bulk food allocation"""
    food_id = fields.String(required=True)
    registration_ids = fields.List(fields.String(), required=True, validate=validate.Length(min=1))
    category_id = fields.String(required=False)  # Optional: allocate to all in category


# Error Schema
class ErrorSchema(Schema):
    """Schema for error responses"""
    code = fields.String()
    message = fields.String()
    details = fields.Dict(allow_none=True)


class ValidationErrorSchema(Schema):
    """Schema for validation error responses"""
    error = fields.Nested(ErrorSchema)


# Wrapper Schemas for {data: {schema}} pattern
class RequestWrapperSchema(Schema):
    """Base wrapper schema for all requests"""
    data = fields.Dict(required=True)


class ResponseWrapperSchema(Schema):
    """Base wrapper schema for all responses"""
    data = fields.Dict(required=True)


# Specific Request Wrappers
class UserRegistrationRequestSchema(Schema):
    """Wrapper for user registration request"""
    data = fields.Nested(UserRegistrationSchema, required=True)


class UserLoginRequestSchema(Schema):
    """Wrapper for user login request"""
    data = fields.Nested(UserLoginSchema, required=True)


class CampCreateRequestSchema(Schema):
    """Wrapper for camp creation request"""
    data = fields.Nested(CampCreateSchema, required=True)


class CampUpdateRequestSchema(Schema):
    """Wrapper for camp update request"""
    data = fields.Nested(CampUpdateSchema, required=True)


class ChurchCreateRequestSchema(Schema):
    """Wrapper for church creation request"""
    data = fields.Nested(ChurchCreateSchema, required=True)


class ChurchCreateMultipleRequestSchema(Schema):
    """Wrapper for multiple church creation request"""
    data = fields.List(fields.Nested(ChurchCreateSchema, required=True))


class ChurchUpdateRequestSchema(Schema):
    """Wrapper for church update request"""
    data = fields.Nested(ChurchUpdateSchema, required=True)


class CategoryCreateRequestSchema(Schema):
    """Wrapper for category creation request"""
    data = fields.Nested(CategoryCreateSchema, required=True)


class CategoryUpdateRequestSchema(Schema):
    """Wrapper for category update request"""
    data = fields.Nested(CategoryUpdateSchema, required=True)


class CustomFieldCreateRequestSchema(Schema):
    """Wrapper for custom field creation request"""
    data = fields.Nested(CustomFieldCreateSchema, required=True)


class CustomFieldUpdateRequestSchema(Schema):
    """Wrapper for custom field update request"""
    data = fields.Nested(CustomFieldUpdateSchema, required=True)


class RegistrationLinkCreateRequestSchema(Schema):
    """Wrapper for registration link creation request"""
    data = fields.Nested(RegistrationLinkCreateSchema, required=True)


class RegistrationLinkUpdateRequestSchema(Schema):
    """Wrapper for registration link update request"""
    data = fields.Nested(RegistrationLinkUpdateSchema, required=True)


class RegistrationCreateRequestSchema(Schema):
    """Wrapper for registration creation request"""
    data = fields.Nested(RegistrationCreateSchema, required=True)


class RegistrationUpdateRequestSchema(Schema):
    """Wrapper for registration update request"""
    data = fields.Nested(RegistrationUpdateSchema, required=True)


class PaymentCreateRequestSchema(Schema):
    """Wrapper for payment creation request"""
    data = fields.Nested(PaymentFormSchema, required=True)


# Food Request Wrappers
class FoodCreateRequestSchema(Schema):
    """Wrapper for food creation request"""
    data = fields.Nested(FoodCreateSchema, required=True)


class FoodUpdateRequestSchema(Schema):
    """Wrapper for food update request"""
    data = fields.Nested(FoodUpdateSchema, required=True)


class FoodAllocationCreateRequestSchema(Schema):
    """Wrapper for food allocation creation request"""
    data = fields.Nested(FoodAllocationCreateSchema, required=True)


class BulkFoodAllocationRequestSchema(Schema):
    """Wrapper for bulk food allocation request"""
    data = fields.Nested(BulkFoodAllocationSchema, required=True)


# Specific Response Wrappers
class UserResponseWrapperSchema(Schema):
    """Wrapper for user response"""
    data = fields.Nested(UserResponseSchema, required=True)


class CampResponseWrapperSchema(Schema):
    """Wrapper for camp response"""
    data = fields.Nested(CampResponseSchema, required=True)


class CampStatsResponseWrapperSchema(Schema):
    """Wrapper for camp stats response"""
    data = fields.Nested(CampStatsSchema, required=True)


class ChurchResponseWrapperSchema(Schema):
    """Wrapper for church response"""
    data = fields.Nested(ChurchResponseSchema, required=True)


class CategoryResponseWrapperSchema(Schema):
    """Wrapper for category response"""
    data = fields.Nested(CategoryResponseSchema, required=True)


class CustomFieldResponseWrapperSchema(Schema):
    """Wrapper for custom field response"""
    data = fields.Nested(CustomFieldResponseSchema, required=True)


class RegistrationLinkResponseWrapperSchema(Schema):
    """Wrapper for registration link response"""
    data = fields.Nested(RegistrationLinkResponseSchema, required=True)


class RegistrationResponseWrapperSchema(Schema):
    """Wrapper for registration response"""
    data = fields.Nested(RegistrationResponseSchema, required=True)


class RegistrationFormResponseWrapperSchema(Schema):
    """Wrapper for registration form response"""
    data = fields.Nested(RegistrationFormSchema, required=True)


# Food Response Wrappers
class FoodResponseWrapperSchema(Schema):
    """Wrapper for food response"""
    data = fields.Nested(FoodResponseSchema, required=True)


class FoodAllocationResponseWrapperSchema(Schema):
    """Wrapper for food allocation response"""
    data = fields.Nested(FoodAllocationResponseSchema, required=True)


# List Response Wrappers
class CampListResponseWrapperSchema(Schema):
    """Wrapper for camp list response"""
    data = fields.List(fields.Nested(CampResponseSchema), required=True)


class ChurchListResponseWrapperSchema(Schema):
    """Wrapper for church list response"""
    data = fields.List(fields.Nested(ChurchResponseSchema), required=True)


class CategoryListResponseWrapperSchema(Schema):
    """Wrapper for category list response"""
    data = fields.List(fields.Nested(CategoryResponseSchema), required=True)


class CustomFieldListResponseWrapperSchema(Schema):
    """Wrapper for custom field list response"""
    data = fields.List(fields.Nested(CustomFieldResponseSchema), required=True)


class RegistrationLinkListResponseWrapperSchema(Schema):
    """Wrapper for registration link list response"""
    data = fields.List(fields.Nested(RegistrationLinkResponseSchema), required=True)


class RegistrationListResponseWrapperSchema(Schema):
    """Wrapper for registration list response"""
    data = fields.List(fields.Nested(RegistrationResponseSchema), required=True)


class PaymentListResponseWrapperSchema(Schema):
    """Wrapper for payment response"""
    data = fields.List(fields.Nested(PaymentResponseSchema), required=True)

class PaymentResponseWrapperSchema(Schema):
    """Wrapper for payment response"""
    data = fields.Nested(PaymentResponseSchema, required=True)


class FoodListResponseWrapperSchema(Schema):
    """Wrapper for food list response"""
    data = fields.List(fields.Nested(FoodResponseSchema), required=True)


class FoodAllocationListResponseWrapperSchema(Schema):
    """Wrapper for food allocation list response"""
    data = fields.List(fields.Nested(FoodAllocationResponseSchema), required=True)


class CheckedInRequestSchema(Schema):
    has_checked_in = fields.Boolean(required=True)


class CheckedInRequestWrapperSchema(Schema):
    data = fields.Nested(CheckedInRequestSchema, required=True)


class RegistrationsQuerySchema(Schema):
    church_id = fields.String(required=False)
    category_id = fields.String(required=False)
    custom_field_responses = fields.Dict(required=False)


class OTPRequest(Schema):
    camper_code = fields.String(required=True)
    otp_code = fields.String(required=False)


class OTPRequestWrapperSchema(Schema):
    data = fields.Nested(OTPRequest, required=True)


# Financial Schemas
class FinancialRequestWrapperSchema(Schema):
    data = fields.Nested(FinancialRequestSchema, required=True)


class FinancialResponseWrapperSchema(Schema):
    data = fields.Nested(FinancialResponseSchema, required=True)

class FinancialListResponseWrapperSchema(Schema):
    data = fields.List(fields.Nested(FinancialResponseSchema), required=True)


# Room Schemas
class RoomCreateSchema(Schema):
    """Schema for creating a room"""
    hostel_name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    block = fields.String(validate=validate.Length(max=50))
    room_number = fields.String(required=True, validate=validate.Length(min=1, max=20))
    room_capacity = fields.Integer(validate=validate.Range(min=1))
    is_special_room = fields.Boolean()
    extra_beds = fields.Integer(validate=validate.Range(min=0))
    room_gender = fields.String(required=True, validate=validate.OneOf(['male', 'female', 'other']))
    is_damaged = fields.Boolean()
    misc_info = fields.String()
    adjoining_to = fields.String()


class RoomUpdateSchema(Schema):
    """Schema for updating a room"""
    hostel_name = fields.String(validate=validate.Length(min=1, max=100))
    block = fields.String(validate=validate.Length(max=50))
    room_number = fields.String(validate=validate.Length(min=1, max=20))
    room_capacity = fields.Integer(validate=validate.Range(min=1))
    is_special_room = fields.Boolean()
    extra_beds = fields.Integer(validate=validate.Range(min=0))
    room_gender = fields.String(validate=validate.OneOf(['male', 'female', 'other']))
    is_damaged = fields.Boolean()
    misc_info = fields.String()
    adjoining_to = fields.String()


class RoomResponseSchema(BaseResponseSchema):
    """Schema for room response"""
    hostel_name = fields.String()
    block = fields.String()
    room_number = fields.String()
    room_capacity = fields.Integer()
    is_special_room = fields.Boolean()
    extra_beds = fields.Integer()
    room_gender = fields.String()
    is_damaged = fields.Boolean()
    misc_info = fields.String()
    adjoining_to = fields.String()
    camp_id = fields.String()
    current_occupancy = fields.Integer()
    available_capacity = fields.Integer()
    is_full = fields.Boolean()
    allocations = fields.List(fields.Dict(), required=False)


# Room Allocation Schemas
class RoomAllocationCreateSchema(Schema):
    """Schema for creating a room allocation"""
    room_id = fields.String(required=True)
    registration_ids = fields.List(fields.String(), required=True, validate=validate.Length(min=1))
    notes = fields.String()
    is_active = fields.Boolean(required=False)


class RoomAllocationUpdateSchema(Schema):
    """Schema for updating a room allocation"""
    is_active = fields.Boolean()
    notes = fields.String()


class RoomAllocationResponseSchema(BaseResponseSchema):
    """Schema for room allocation response"""
    room_id = fields.String()
    registration_id = fields.String()
    camp_id = fields.String()
    allocated_by = fields.String()
    allocation_date = fields.DateTime()
    is_active = fields.Boolean()
    notes = fields.String()
    room = fields.Nested(RoomResponseSchema, required=False)
    registration = fields.Nested(RegistrationResponseSchema, required=False)
    allocator_name = fields.String(required=False)


# Request Wrapper Schemas
class RoomCreateRequestSchema(Schema):
    """Wrapper for room creation request"""
    data = fields.Nested(RoomCreateSchema, required=True)


class RoomUpdateRequestSchema(Schema):
    """Wrapper for room update request"""
    data = fields.Nested(RoomUpdateSchema, required=True)


class RoomAllocationCreateRequestSchema(Schema):
    """Wrapper for room allocation creation request"""
    data = fields.Nested(RoomAllocationCreateSchema, required=True)


class RoomAllocationUpdateRequestSchema(Schema):
    """Wrapper for room allocation update request"""
    data = fields.Nested(RoomAllocationUpdateSchema, required=True)


# Response Wrapper Schemas
class RoomResponseWrapperSchema(Schema):
    """Wrapper for room response"""
    data = fields.Nested(RoomResponseSchema, required=True)


class RoomListResponseWrapperSchema(Schema):
    """Wrapper for room list response"""
    data = fields.List(fields.Nested(RoomResponseSchema), required=True)


class RoomAllocationResponseWrapperSchema(Schema):
    """Wrapper for room allocation response"""
    data = fields.Nested(RoomAllocationResponseSchema, required=True)


class RoomAllocationListResponseWrapperSchema(Schema):
    """Wrapper for room allocation list response"""
    data = fields.List(fields.Nested(RoomAllocationResponseSchema), required=True)
