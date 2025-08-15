from apiflask import Schema
from marshmallow import fields, validate
from app._shared.schemas import BaseResponseSchema


# User Schemas
class UserRegistrationSchema(Schema):
    """Schema for user registration"""
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate.Length(min=8))
    full_name = fields.String(required=True, validate=validate.Length(min=2))
    role = fields.String(validate=validate.OneOf(['camp_manager', 'volunteer']))
    camp_id = fields.String(required=False, allow_none=True)


class UserLoginSchema(Schema):
    """Schema for user login"""
    email = fields.Email(required=True)
    password = fields.String(required=True)


class UserResponseSchema(BaseResponseSchema):
    """Schema for user response"""
    email = fields.Email()
    full_name = fields.String()
    role = fields.String()


# Specific Request Wrappers
class UserRegistrationRequestSchema(Schema):
    """Wrapper for user registration request"""
    data = fields.Nested(UserRegistrationSchema, required=True)


class UserLoginRequestSchema(Schema):
    """Wrapper for user login request"""
    data = fields.Nested(UserLoginSchema, required=True)


class UserResponseWrapperSchema(Schema):
    """Wrapper for user response"""
    data = fields.Nested(UserResponseSchema, required=True)