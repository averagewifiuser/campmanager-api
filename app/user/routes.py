from apiflask import APIBlueprint
from flask import request, current_app
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity, create_refresh_token
from datetime import timedelta

from app._shared.schemas import SuccessMessageWrapperSchema, ErrorResponseWrapperSchema
from .schemas import (
    UserRegistrationRequestSchema,
    UserLoginRequestSchema,
    UserResponseWrapperSchema
)
from .services import UserService


# Create APIBlueprint for automatic OpenAPI documentation
user_bp = APIBlueprint('user', __name__, url_prefix='/auth')

# Initialize user service
user_service = UserService()


@user_bp.get('/users')
@user_bp.output(UserResponseWrapperSchema)
@user_bp.doc(
    summary='Get all users',
    description='Get a list of all users'
)
@jwt_required()
def get_users():
    """Get all users"""
    try:
        users = user_service.get_all_users()
        return {
            'data': [user.to_dict(for_api=True) for user in users]
        }, 200
    except Exception as e:
        current_app.logger.error(f"Get users error: {str(e)}")
        return {
            'data': {
                'code': 'GET_USERS_ERROR',
                'message': 'Failed to get users',
                'details': {'error': str(e)}
            }
        }, 500

@user_bp.post('/register')
@user_bp.input(UserRegistrationRequestSchema)
@user_bp.doc(
    summary='Register a new user',
    description='Create a new user account for camp managers or volunteers'
)
def register(json_data):
    """Register a new user"""
    from flask import jsonify
    
    try:
        # Extract data from wrapper
        user_data = json_data['data']
        
        # Create new user (service will handle duplicate check)
        new_user = user_service.create_user(user_data)
        
        return jsonify({
            'data': new_user.to_dict(for_api=True)
        }), 201
        
    except ValueError as e:
        # Handle validation errors from service
        current_app.logger.warning(f"Registration validation error: {str(e)}")
        if "already exists" in str(e):
            return jsonify({
                'data': {
                    'code': 'USER_EXISTS',
                    'message': 'User with this email already exists',
                    'details': {'email': user_data.get('email')}
                }
            }), 409
        else:
            return jsonify({
                'data': {
                    'code': 'VALIDATION_ERROR',
                    'message': str(e),
                    'details': None
                }
            }), 400
    except Exception as e:
        current_app.logger.error(f"Registration error: {str(e)}")
        return jsonify({
            'data': {
                'code': 'REGISTRATION_ERROR',
                'message': 'Failed to register user',
                'details': {'error': str(e)}
            }
        }), 500


@user_bp.post('/login')
@user_bp.input(UserLoginRequestSchema)
@user_bp.doc(
    summary='User login',
    description='Authenticate user and return JWT tokens'
)
def login(json_data):
    """Authenticate user and return JWT tokens"""
    from flask import jsonify
    
    try:
        # Extract credentials from wrapper
        credentials = json_data['data']
        
        # Authenticate user
        user = user_service.authenticate_user(
            credentials['email'], 
            credentials['password']
        )
        
        if not user:
            return jsonify({
                'data': {
                    'code': 'INVALID_CREDENTIALS',
                    'message': 'Invalid email or password',
                    'details': None
                }
            }), 401
        
        # Create JWT tokens - don't use additional_claims here, let the callback handle it
        access_token = create_access_token(
            identity=str(user.id),
            expires_delta=timedelta(hours=24)
        )
        
        refresh_token = create_refresh_token(
            identity=str(user.id),
            expires_delta=timedelta(days=30)
        )
        
        return jsonify({
            'data': {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': user.to_dict(),
                'expires_in': 86400  # 24 hours in seconds
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}")
        return jsonify({
            'data': {
                'code': 'LOGIN_ERROR',
                'message': 'Login failed',
                'details': {'error': str(e)}
            }
        }), 500


@user_bp.post('/refresh')
@user_bp.output({
    '200': {
        'description': 'Token refresh successful',
        'schema': {
            'type': 'object',
            'properties': {
                'data': {
                    'type': 'object',
                    'properties': {
                        'access_token': {'type': 'string'},
                        'expires_in': {'type': 'integer'}
                    }
                }
            }
        }
    },
    '401': ErrorResponseWrapperSchema
})
@user_bp.doc(
    summary='Refresh access token',
    description='Get a new access token using refresh token'
)
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get user to include in token claims
        user = user_service.get_user_by_id(current_user_id)
        if not user:
            return {
                'data': {
                    'code': 'USER_NOT_FOUND',
                    'message': 'User not found',
                    'details': None
                }
            }, 401
        
        # Create new access token
        access_token = create_access_token(
            identity=current_user_id,
            additional_claims={
                'email': user.email,
                'role': user.role,
                'full_name': user.full_name
            },
            expires_delta=timedelta(hours=24)
        )
        
        return {
            'data': {
                'access_token': access_token,
                'expires_in': 86400  # 24 hours in seconds
            }
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Token refresh error: {str(e)}")
        return {
            'data': {
                'code': 'REFRESH_ERROR',
                'message': 'Token refresh failed',
                'details': {'error': str(e)}
            }
        }, 500


@user_bp.post('/logout')
@user_bp.output(SuccessMessageWrapperSchema)
@user_bp.doc(
    summary='User logout',
    description='Logout user (client should discard tokens)'
)
@jwt_required()
def logout():
    """Logout user"""
    try:
        # Note: In a production app, you might want to blacklist the token
        # For now, we'll just return success and let client handle token removal
        
        return {
            'data': {
                'message': 'Successfully logged out'
            }
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Logout error: {str(e)}")
        return {
            'data': {
                'code': 'LOGOUT_ERROR',
                'message': 'Logout failed',
                'details': {'error': str(e)}
            }
        }, 500


@user_bp.get('/me')
@user_bp.output(UserResponseWrapperSchema)
@user_bp.doc(
    summary='Get current user',
    description='Get details of the currently authenticated user'
)
@jwt_required()
def get_current_user():
    """Get current user details"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get user details
        user = user_service.get_user_by_id(current_user_id)
        if not user:
            return {
                'data': {
                    'code': 'USER_NOT_FOUND',
                    'message': 'User not found',
                    'details': None
                }
            }, 404
        
        return {
            'data': user.to_dict(for_api=True)
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Get current user error: {str(e)}")
        return {
            'data': {
                'code': 'GET_USER_ERROR',
                'message': 'Failed to get user details',
                'details': {'error': str(e)}
            }
        }, 500


@user_bp.put('/me')
@user_bp.input({
    'type': 'object',
    'properties': {
        'data': {
            'type': 'object',
            'properties': {
                'full_name': {'type': 'string', 'minLength': 2, 'maxLength': 255},
                'email': {'type': 'string', 'format': 'email'}
            }
        }
    },
    'required': ['data']
})
@user_bp.output(UserResponseWrapperSchema)
@user_bp.doc(
    summary='Update current user',
    description='Update details of the currently authenticated user'
)
@jwt_required()
def update_current_user(json_data):
    """Update current user details"""
    try:
        current_user_id = get_jwt_identity()
        update_data = json_data['data']
        
        # Check if email is being changed and already exists
        if 'email' in update_data:
            existing_user = user_service.get_user_by_email(update_data['email'])
            if existing_user and str(existing_user.id) != current_user_id:
                return {
                    'data': {
                        'code': 'EMAIL_EXISTS',
                        'message': 'Email already exists',
                        'details': {'email': update_data['email']}
                    }
                }, 409
        
        # Update user
        updated_user = user_service.update_user(current_user_id, update_data)
        if not updated_user:
            return {
                'data': {
                    'code': 'USER_NOT_FOUND',
                    'message': 'User not found',
                    'details': None
                }
            }, 404
        
        return {
            'data': updated_user.to_dict(for_api=True)
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Update user error: {str(e)}")
        return {
            'data': {
                'code': 'UPDATE_USER_ERROR',
                'message': 'Failed to update user',
                'details': {'error': str(e)}
            }
        }, 500


@user_bp.put('/me/password')
@user_bp.input({
    'type': 'object',
    'properties': {
        'data': {
            'type': 'object',
            'properties': {
                'current_password': {'type': 'string'},
                'new_password': {'type': 'string', 'minLength': 8}
            },
            'required': ['current_password', 'new_password']
        }
    },
    'required': ['data']
})
@user_bp.output(SuccessMessageWrapperSchema)
@user_bp.doc(
    summary='Change password',
    description='Change password for the currently authenticated user'
)
@jwt_required()
def change_password(json_data):
    """Change user password"""
    try:
        current_user_id = get_jwt_identity()
        password_data = json_data['data']
        
        # Verify current password and update
        success = user_service.change_password(
            current_user_id,
            password_data['current_password'],
            password_data['new_password']
        )
        
        if not success:
            return {
                'data': {
                    'code': 'INVALID_PASSWORD',
                    'message': 'Current password is incorrect',
                    'details': None
                }
            }, 400
        
        return {
            'data': {
                'message': 'Password changed successfully'
            }
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Change password error: {str(e)}")
        return {
            'data': {
                'code': 'CHANGE_PASSWORD_ERROR',
                'message': 'Failed to change password',
                'details': {'error': str(e)}
            }
        }, 500


# Error handlers for the user blueprint
# @user_bp.errorhandler(400)
# def bad_request(error):
#     """Handle bad request errors"""
#     return {
#         'data': {
#             'code': 'BAD_REQUEST',
#             'message': 'Bad request',
#             'details': {'error': str(error)}
#         }
#     }, 400


# @user_bp.errorhandler(422)
# def validation_error(error):
#     """Handle validation errors"""
#     return {
#         'data': {
#             'code': 'VALIDATION_ERROR',
#             'message': 'Validation failed',
#             'details': error.description if hasattr(error, 'description') else {'error': str(error)}
#         }
#     }, 422


# @user_bp.errorhandler(500)
# def internal_error(error):
#     """Handle internal server errors"""
#     current_app.logger.error(f"Internal error in user routes: {str(error)}")
#     return {
#         'data': {
#             'code': 'INTERNAL_ERROR',
#             'message': 'Internal server error',
#             'details': None
#         }
#     }, 500
