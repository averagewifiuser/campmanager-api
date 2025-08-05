from typing import Any

from apiflask import Schema, fields
# from apiflask.validators import Range
# from marshmallow.exceptions import ValidationError

# from .api_errors import BaseError


# Base Schemas
class BaseResponseSchema(Schema):
    """Base response schema with common fields"""
    id = fields.String(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    # def handle_error(self, error: ValidationError, data: Any, *, many: bool, **kwargs):
    #     raise BaseError(error.normalized_messages(), error_code=422, payload=error.normalized_messages())


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


# Success Message Schema
class SuccessMessageSchema(Schema):
    """Schema for success messages"""
    message = fields.String()


class SuccessMessageWrapperSchema(Schema):
    """Wrapper for success messages"""
    data = fields.Nested(SuccessMessageSchema, required=True)


# Error Response Wrapper
class ErrorResponseWrapperSchema(Schema):
    """Wrapper for error responses"""
    data = fields.Nested(ErrorSchema, required=True)


# Pagination Schema
class PaginationSchema(Schema):
    """Schema for pagination metadata"""
    page = fields.Integer()
    per_page = fields.Integer()
    total = fields.Integer()
    pages = fields.Integer()
    has_prev = fields.Boolean()
    has_next = fields.Boolean()
    prev_num = fields.Integer(allow_none=True)
    next_num = fields.Integer(allow_none=True)


# Paginated Response Schema
class PaginatedResponseSchema(Schema):
    """Schema for paginated responses with data wrapper"""
    items = fields.List(fields.Raw())
    pagination = fields.Nested(PaginationSchema)


class PaginatedResponseWrapperSchema(Schema):
    """Wrapper for paginated responses"""
    data = fields.Nested(PaginatedResponseSchema, required=True)