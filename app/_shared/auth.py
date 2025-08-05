from functools import wraps
from typing import Callable, Optional
import uuid

from flask import current_app, g, request
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request

from app.user.models import User
from .api_errors import AuthenticationError, AuthorizationError, ValidationError
import traceback


def token_required(f: Callable) -> Callable:
    """
    Decorator to require valid JWT token for endpoint access
    Sets current_user in flask.g for use in views
    """
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        try:
            # Get user ID from JWT token
            current_user_id = get_jwt_identity()
            
            # Fetch user from database
            user = User.query.filter_by(id=current_user_id).first()
            if not user:
                current_app.logger.warning(f"Token contains invalid user ID: {current_user_id}")
                raise AuthenticationError("Invalid user token")
            
            # Store user in flask.g for access in views
            g.current_user = user
            g.current_user_id = str(user.id)
            
            return f(*args, **kwargs)
            
        except Exception as e:
            current_app.logger.error(f"Token validation error: {str(e)}")
            current_app.logger.error(traceback.format_exc())
            return {
                'data': {
                    'code': 'AUTHENTICATION_ERROR',
                    'message': 'Authentication required',
                    'details': None
                }
            }, 401
    
    return decorated_function


def role_required(*required_roles: str) -> Callable:
    """
    Decorator to require specific user roles for endpoint access
    Must be used with @token_required or @jwt_required
    
    Args:
        *required_roles: Variable number of role strings that are allowed
        
    Usage:
        @role_required('camp_manager')
        @role_required('camp_manager', 'volunteer')
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Ensure we have a current user (from token_required)
                if not hasattr(g, 'current_user') or not g.current_user:
                    # Try to get user if token_required wasn't used
                    current_user_id = get_jwt_identity()
                    user = User.query.filter_by(id=current_user_id).first()
                    if not user:
                        raise AuthorizationError("User not found")
                    g.current_user = user
                
                # Check if user has required role
                user_role = g.current_user.role
                if user_role not in required_roles:
                    current_app.logger.warning(
                        f"Access denied for user {g.current_user.email} with role {user_role}. "
                        f"Required roles: {required_roles}"
                    )
                    raise AuthorizationError(
                        f"Access denied. Required role(s): {', '.join(required_roles)}"
                    )
                
                return f(*args, **kwargs)
                
            except AuthorizationError:
                return {
                    'data': {
                        'code': 'AUTHORIZATION_ERROR',
                        'message': f"Access denied. Required role(s): {', '.join(required_roles)}",
                        'details': {'required_roles': list(required_roles)}
                    }
                }, 403
            except Exception as e:
                current_app.logger.error(f"Role validation error: {str(e)}")
                return {
                    'data': {
                        'code': 'AUTHORIZATION_ERROR',
                        'message': 'Access denied',
                        'details': None
                    }
                }, 403
        
        return decorated_function
    return decorator


def camp_owner_required(camp_id_param: str = 'camp_id') -> Callable:
    """
    Decorator to ensure user owns/manages the specified camp
    Must be used with @token_required
    
    Args:
        camp_id_param: Name of the parameter containing camp_id (default: 'camp_id')
        
    Usage:
        @camp_owner_required()  # Uses 'camp_id' from URL params
        @camp_owner_required('id')  # Uses 'id' from URL params
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Ensure we have a current user
                if not hasattr(g, 'current_user') or not g.current_user:
                    raise AuthorizationError("Authentication required")
                
                # Get camp_id from kwargs (URL parameters)
                camp_id = kwargs.get(camp_id_param)
                if not camp_id:
                    raise ValidationError(f"Missing {camp_id_param} parameter")
                
                # Validate camp_id format
                try:
                    uuid.UUID(camp_id)
                except ValueError:
                    raise ValidationError("Invalid camp ID format")
                
                # Import here to avoid circular imports
                from ..camp.models import Camp
                
                # Check if camp exists and user owns it
                camp = Camp.query.filter_by(id=camp_id).first()
                if not camp:
                    return {
                        'data': {
                            'code': 'CAMP_NOT_FOUND',
                            'message': 'Camp not found',
                            'details': None
                        }
                    }, 404
                
                # Check ownership
                if str(camp.camp_manager_id) != str(g.current_user.id):
                    current_app.logger.warning(
                        f"Access denied: User {g.current_user.email} tried to access "
                        f"camp {camp_id} owned by {camp.camp_manager_id}"
                    )
                    raise AuthorizationError("You can only access your own camps")
                
                # Store camp in g for use in view
                g.current_camp = camp
                
                return f(*args, **kwargs)
                
            except (AuthorizationError, ValidationError) as e:
                return {
                    'data': {
                        'code': 'AUTHORIZATION_ERROR',
                        'message': str(e),
                        'details': None
                    }
                }, 403
            except Exception as e:
                current_app.logger.error(f"Camp ownership validation error: {str(e)}")
                return {
                    'data': {
                        'code': 'AUTHORIZATION_ERROR',
                        'message': 'Access denied',
                        'details': None
                    }
                }, 403
        
        return decorated_function
    return decorator


def optional_auth(f: Callable) -> Callable:
    """
    Decorator for endpoints that work with or without authentication
    Sets current_user in flask.g if valid token is provided
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Try to verify JWT, but don't fail if it's missing
            verify_jwt_in_request(optional=True)
            
            current_user_id = get_jwt_identity()
            if current_user_id:
                user = User.query.filter_by(id=current_user_id).first()
                if user:
                    g.current_user = user
                    g.current_user_id = str(user.id)
                else:
                    g.current_user = None
                    g.current_user_id = None
            else:
                g.current_user = None
                g.current_user_id = None
                
        except Exception:
            # If token is invalid, just continue without authentication
            g.current_user = None
            g.current_user_id = None
        
        return f(*args, **kwargs)
    
    return decorated_function



# Utility functions for use in views
def get_current_user() -> Optional[User]:
    """Get the current authenticated user from flask.g"""
    return getattr(g, 'current_user', None)


def get_current_user_id() -> Optional[str]:
    """Get the current authenticated user ID from flask.g"""
    return getattr(g, 'current_user_id', None)


def get_current_camp():
    """Get the current camp from flask.g (set by camp_owner_required)"""
    return getattr(g, 'current_camp', None)


def require_camp_manager(user: Optional[User] = None) -> bool:
    """Check if user is a camp manager"""
    if not user:
        user = get_current_user()
    return user and user.role == 'camp_manager'


def require_volunteer_or_manager(user: Optional[User] = None) -> bool:
    """Check if user is a volunteer or camp manager"""
    if not user:
        user = get_current_user()
    return user and user.role in ['volunteer', 'camp_manager']


class AuthMiddleware:
    """
    Middleware class for handling authentication across the application
    """
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the middleware with the Flask app"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
    
    def before_request(self):
        """Process requests before they reach the view functions"""
        # Initialize auth-related variables in g
        g.current_user = None
        g.current_user_id = None
        g.current_camp = None
        
        # Log request for debugging (remove in production)
        if current_app.debug:
            current_app.logger.debug(f"{request.method} {request.path} - {request.remote_addr}")
    
    def after_request(self, response):
        """Process responses after view functions complete"""
        # Add security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Add CORS headers if needed (configure domains in production)
        if current_app.debug:
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        
        return response
