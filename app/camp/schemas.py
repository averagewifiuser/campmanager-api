
from apiflask import Schema
from marshmallow import fields, validate, validates, ValidationError
from datetime import datetime
import re

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

