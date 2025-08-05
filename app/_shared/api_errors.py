from flask import jsonify
from werkzeug.http import HTTP_STATUS_CODES


def success_response(status_code=200, data=None, message="success", pagination=None):
    return response_builder(
        status_code=status_code, message=message, data=data, pagination=pagination
    )


def response_builder(status_code, message=None, data=None, pagination=None):
    if status_code > 299:
        payload = {"error": HTTP_STATUS_CODES.get(status_code, "Unknown error")}
    else:
        payload = {}

    if message:
        payload["message"] = message

    if pagination:
        payload["pagination"] = pagination

    payload["data"] = data

    response = jsonify(payload)
    response.status_code = status_code
    return response


def bad_request(message="Bad Request"):
    return response_builder(400, message)


def unauthorized_request(message="You're not allowed to do that!"):
    return response_builder(401, message)


def permissioned_denied(message="You don't have the permissions to do that!"):
    return response_builder(403, message)


def server_error(
    message="Something went wrong! Our backend team has been notified and are working to resolve it.",
):
    return response_builder(500, message)


def not_found(message="The object was not found!"):
    return response_builder(404, message)


"""
Custom API Error Classes

This module defines custom exception classes for the CampManager API
that provide consistent error handling and response formatting.
"""

from typing import Dict, Any, Optional


class APIError(Exception):
    """Base API error class"""
    
    def __init__(self, message: str, code: str = None, details: Dict[str, Any] = None, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__.upper()
        self.details = details
        self.status_code = status_code
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format"""
        return {
            'code': self.code,
            'message': self.message,
            'details': self.details
        }
    
    def to_response(self) -> tuple:
        """Convert error to API response format"""
        return {
            'data': self.to_dict()
        }, self.status_code


class ValidationError(APIError):
    """Raised when input validation fails"""
    
    def __init__(self, message: str = "Validation failed", field: str = None, details: Dict[str, Any] = None):
        if field and not details:
            details = {'field': field}
        elif field and details:
            details['field'] = field
        
        super().__init__(
            message=message,
            code='VALIDATION_ERROR',
            details=details,
            status_code=400
        )


class AuthenticationError(APIError):
    """Raised when authentication fails"""
    
    def __init__(self, message: str = "Authentication failed", details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            code='AUTHENTICATION_ERROR',
            details=details,
            status_code=401
        )


class AuthorizationError(APIError):
    """Raised when authorization fails"""
    
    def __init__(self, message: str = "Access denied", details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            code='AUTHORIZATION_ERROR',
            details=details,
            status_code=403
        )


class NotFoundError(APIError):
    """Raised when a resource is not found"""
    
    def __init__(self, message: str = "Resource not found", resource: str = None, details: Dict[str, Any] = None):
        if resource and not details:
            details = {'resource': resource}
        elif resource and details:
            details['resource'] = resource
        
        super().__init__(
            message=message,
            code='NOT_FOUND',
            details=details,
            status_code=404
        )


class ConflictError(APIError):
    """Raised when there's a resource conflict"""
    
    def __init__(self, message: str = "Resource conflict", details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            code='CONFLICT',
            details=details,
            status_code=409
        )


class BusinessRuleError(APIError):
    """Raised when business rules are violated"""
    
    def __init__(self, message: str, rule: str = None, details: Dict[str, Any] = None):
        if rule and not details:
            details = {'rule': rule}
        elif rule and details:
            details['rule'] = rule
        
        super().__init__(
            message=message,
            code='BUSINESS_RULE_ERROR',
            details=details,
            status_code=422
        )


class RateLimitError(APIError):
    """Raised when rate limits are exceeded"""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None, details: Dict[str, Any] = None):
        if retry_after and not details:
            details = {'retry_after': retry_after}
        elif retry_after and details:
            details['retry_after'] = retry_after
        
        super().__init__(
            message=message,
            code='RATE_LIMIT_EXCEEDED',
            details=details,
            status_code=429
        )


class ExternalServiceError(APIError):
    """Raised when external service calls fail"""
    
    def __init__(self, message: str = "External service error", service: str = None, details: Dict[str, Any] = None):
        if service and not details:
            details = {'service': service}
        elif service and details:
            details['service'] = service
        
        super().__init__(
            message=message,
            code='EXTERNAL_SERVICE_ERROR',
            details=details,
            status_code=502
        )


class DatabaseError(APIError):
    """Raised when database operations fail"""
    
    def __init__(self, message: str = "Database operation failed", operation: str = None, details: Dict[str, Any] = None):
        if operation and not details:
            details = {'operation': operation}
        elif operation and details:
            details['operation'] = operation
        
        super().__init__(
            message=message,
            code='DATABASE_ERROR',
            details=details,
            status_code=500
        )


class ConfigurationError(APIError):
    """Raised when there are configuration issues"""
    
    def __init__(self, message: str = "Configuration error", config_key: str = None, details: Dict[str, Any] = None):
        if config_key and not details:
            details = {'config_key': config_key}
        elif config_key and details:
            details['config_key'] = config_key
        
        super().__init__(
            message=message,
            code='CONFIGURATION_ERROR',
            details=details,
            status_code=500
        )


# Camp-specific errors
class CampError(APIError):
    """Base class for camp-related errors"""
    pass


class CampNotFoundError(NotFoundError):
    """Raised when a camp is not found"""
    
    def __init__(self, camp_id: str = None):
        message = f"Camp not found"
        if camp_id:
            message += f": {camp_id}"
        
        super().__init__(
            message=message,
            resource='camp',
            details={'camp_id': camp_id} if camp_id else None
        )


class CampCapacityError(BusinessRuleError):
    """Raised when camp capacity is exceeded"""
    
    def __init__(self, current_count: int = None, capacity: int = None):
        message = "Camp is at full capacity"
        details = {}
        
        if current_count is not None:
            details['current_registrations'] = current_count
        if capacity is not None:
            details['capacity'] = capacity
        
        super().__init__(
            message=message,
            rule='capacity_limit',
            details=details if details else None
        )


class RegistrationDeadlineError(BusinessRuleError):
    """Raised when registration deadline has passed"""
    
    def __init__(self, deadline: str = None):
        message = "Registration deadline has passed"
        details = {'deadline': deadline} if deadline else None
        
        super().__init__(
            message=message,
            rule='registration_deadline',
            details=details
        )


# Registration Link specific errors
class RegistrationLinkError(APIError):
    """Base class for registration link errors"""
    pass


class InvalidLinkTokenError(NotFoundError):
    """Raised when registration link token is invalid"""
    
    def __init__(self, token: str = None):
        message = "Invalid registration link"
        details = {'token': token} if token else None
        
        super().__init__(
            message=message,
            resource='registration_link',
            details=details
        )


class LinkExpiredError(BusinessRuleError):
    """Raised when registration link has expired"""
    
    def __init__(self, expired_at: str = None):
        message = "Registration link has expired"
        details = {'expired_at': expired_at} if expired_at else None
        
        super().__init__(
            message=message,
            rule='link_expiration',
            details=details
        )


class LinkUsageLimitError(BusinessRuleError):
    """Raised when registration link usage limit is reached"""
    
    def __init__(self, usage_count: int = None, usage_limit: int = None):
        message = "Registration link usage limit reached"
        details = {}
        
        if usage_count is not None:
            details['usage_count'] = usage_count
        if usage_limit is not None:
            details['usage_limit'] = usage_limit
        
        super().__init__(
            message=message,
            rule='usage_limit',
            details=details if details else None
        )


# User specific errors
class UserError(APIError):
    """Base class for user-related errors"""
    pass


class UserNotFoundError(NotFoundError):
    """Raised when a user is not found"""
    
    def __init__(self, user_id: str = None, email: str = None):
        message = "User not found"
        details = {}
        
        if user_id:
            details['user_id'] = user_id
        if email:
            details['email'] = email
        
        super().__init__(
            message=message,
            resource='user',
            details=details if details else None
        )


class EmailAlreadyExistsError(ConflictError):
    """Raised when trying to register with an existing email"""
    
    def __init__(self, email: str):
        super().__init__(
            message=f"User with email {email} already exists",
            details={'email': email}
        )


class InvalidCredentialsError(AuthenticationError):
    """Raised when login credentials are invalid"""
    
    def __init__(self):
        super().__init__(
            message="Invalid email or password"
        )


# Payment specific errors
class PaymentError(APIError):
    """Base class for payment-related errors"""
    pass


class PaymentProcessingError(ExternalServiceError):
    """Raised when payment processing fails"""
    
    def __init__(self, transaction_id: str = None, provider: str = None):
        message = "Payment processing failed"
        details = {}
        
        if transaction_id:
            details['transaction_id'] = transaction_id
        if provider:
            details['provider'] = provider
        
        super().__init__(
            message=message,
            service='payment_processor',
            details=details if details else None
        )


# Utility functions
def handle_api_error(error: APIError) -> tuple:
    """Convert API error to Flask response"""
    return error.to_response()


def create_error_response(code: str, message: str, details: Dict[str, Any] = None, status_code: int = 400) -> tuple:
    """Create a standardized error response"""
    return {
        'data': {
            'code': code,
            'message': message,
            'details': details
        }
    }, status_code