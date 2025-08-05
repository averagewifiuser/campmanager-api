from flask import request, current_app
from apiflask import APIBlueprint
from flask_jwt_extended import jwt_required

from .models import Camp, Church, Category, CustomField, RegistrationLink, Registration
from .schemas import (
    # Camp schemas
    CampCreateRequestSchema,
    CampUpdateRequestSchema,
    CampResponseWrapperSchema,
    CampListResponseWrapperSchema,
    CampStatsResponseWrapperSchema,
    
    # Church schemas
    ChurchCreateRequestSchema,
    ChurchUpdateRequestSchema,
    ChurchResponseWrapperSchema,
    ChurchListResponseWrapperSchema,
    
    # Category schemas
    CategoryCreateRequestSchema,
    CategoryUpdateRequestSchema,
    CategoryResponseWrapperSchema,
    CategoryListResponseWrapperSchema,
    
    # Custom Field schemas
    CustomFieldCreateRequestSchema,
    CustomFieldUpdateRequestSchema,
    CustomFieldResponseWrapperSchema,
    CustomFieldListResponseWrapperSchema,
    
    # Registration Link schemas
    RegistrationLinkCreateRequestSchema,
    RegistrationLinkUpdateRequestSchema,
    RegistrationLinkResponseWrapperSchema,
    RegistrationLinkListResponseWrapperSchema,
    
    # Registration schemas
    RegistrationCreateRequestSchema,
    RegistrationUpdateRequestSchema,
    RegistrationResponseWrapperSchema,
    RegistrationListResponseWrapperSchema,
    RegistrationFormResponseWrapperSchema,
)
from app._shared.schemas import SuccessMessageWrapperSchema
from .services import CampService, ChurchService, CategoryService, CustomFieldService, RegistrationLinkService, RegistrationService
from .._shared.auth import token_required, role_required, camp_owner_required, optional_auth, get_current_user


# Create APIBlueprint for camp management
camp_bp = APIBlueprint('camp', __name__, url_prefix='/camps')

# Initialize services
camp_service = CampService()
church_service = ChurchService()
category_service = CategoryService()
custom_field_service = CustomFieldService()
registration_link_service = RegistrationLinkService()
registration_service = RegistrationService()


# =============================================================================
# CAMP ROUTES
# =============================================================================

@camp_bp.get('')
@camp_bp.output(CampListResponseWrapperSchema)
@camp_bp.doc(
    summary='Get camps for current user',
    description='Retrieve all camps managed by the authenticated user'
)
@token_required
@role_required('camp_manager')
def get_camps():
    """Get camps for current user"""
    try:
        user = get_current_user()
        camps = camp_service.get_user_camps(str(user.id))
        
        return {
            'data': [camp.to_dict() for camp in camps]
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Get camps error: {str(e)}")
        return {
            'data': {
                'code': 'GET_CAMPS_ERROR',
                'message': 'Failed to retrieve camps',
                'details': {'error': str(e)}
            }
        }, 500

@camp_bp.post('/<camp_id>/custom-fields')
@camp_bp.input(CustomFieldCreateRequestSchema)
@camp_bp.output(CustomFieldResponseWrapperSchema, status_code=201)
@camp_bp.doc(
    summary='Create custom field',
    description='Create a new custom field for a camp'
)
@token_required
@camp_owner_required()
def create_custom_field(camp_id, json_data):
    """Create custom field"""
    try:
        field_data = json_data['data']
        field_data['camp_id'] = camp_id
        
        new_field = custom_field_service.create_custom_field(field_data)
        
        return {
            'data': new_field.to_dict()
        }, 201
        
    except ValueError as e:
        return {
            'data': {
                'code': 'VALIDATION_ERROR',
                'message': str(e),
                'details': None
            }
        }, 400
    except Exception as e:
        current_app.logger.error(f"Create custom field error: {str(e)}")
        return {
            'data': {
                'code': 'CREATE_CUSTOM_FIELD_ERROR',
                'message': 'Failed to create custom field',
                'details': {'error': str(e)}
            }
        }, 500
        
@camp_bp.get('/registration-links/<link_id>')
@camp_bp.output(RegistrationLinkResponseWrapperSchema)
@camp_bp.doc(
    summary='Get registration link details',
    description='Get details of a specific registration link'
)
@token_required
def get_registration_link(link_id):
    """Get registration link details"""
    try:
        # Verify user owns the camp that owns this registration link
        link = registration_link_service.get_registration_link_by_id(link_id)
        if not link:
            return {
                'data': {
                    'code': 'LINK_NOT_FOUND',
                    'message': 'Registration link not found',
                    'details': None
                }
            }, 404
        
        # Check if user owns the camp
        user = get_current_user()
        if str(link.camp.camp_manager_id) != str(user.id):
            return {
                'data': {
                    'code': 'AUTHORIZATION_ERROR',
                    'message': 'Access denied',
                    'details': None
                }
            }, 403
        
        return {
            'data': link.to_dict()
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Get registration link error: {str(e)}")
        return {
            'data': {
                'code': 'GET_LINK_ERROR',
                'message': 'Failed to retrieve registration link',
                'details': {'error': str(e)}
            }
        }, 500
# =============================================================================
# INDIVIDUAL REGISTRATION ROUTES
# =============================================================================

@camp_bp.get('/registrations/<registration_id>')
@camp_bp.output(RegistrationResponseWrapperSchema)
@camp_bp.doc(
    summary='Get registration details',
    description='Get details of a specific registration'
)
@token_required
def get_registration(registration_id):
    """Get registration details"""
    try:
        # Verify user owns the camp that owns this registration
        registration = registration_service.get_registration_by_id(registration_id)
        if not registration:
            return {
                'data': {
                    'code': 'REGISTRATION_NOT_FOUND',
                    'message': 'Registration not found',
                    'details': None
                }
            }, 404
        
        # Check if user owns the camp
        user = get_current_user()
        if str(registration.camp.camp_manager_id) != str(user.id):
            return {
                'data': {
                    'code': 'AUTHORIZATION_ERROR',
                    'message': 'Access denied',
                    'details': None
                }
            }, 403
        
        return {
            'data': registration.to_dict()
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Get registration error: {str(e)}")
        return {
            'data': {
                'code': 'GET_REGISTRATION_ERROR',
                'message': 'Failed to retrieve registration',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.put('/registrations/<registration_id>')
@camp_bp.input(RegistrationUpdateRequestSchema)
@camp_bp.output(RegistrationResponseWrapperSchema)
@camp_bp.doc(
    summary='Update registration',
    description='Update registration details'
)
@token_required
def update_registration(registration_id, json_data):
    """Update registration"""
    try:
        # Verify user owns the camp that owns this registration
        registration = registration_service.get_registration_by_id(registration_id)
        if not registration:
            return {
                'data': {
                    'code': 'REGISTRATION_NOT_FOUND',
                    'message': 'Registration not found',
                    'details': None
                }
            }, 404
        
        # Check if user owns the camp
        user = get_current_user()
        if str(registration.camp.camp_manager_id) != str(user.id):
            return {
                'data': {
                    'code': 'AUTHORIZATION_ERROR',
                    'message': 'Access denied',
                    'details': None
                }
            }, 403
        
        update_data = json_data['data']
        updated_registration = registration_service.update_registration(registration_id, update_data)
        
        return {
            'data': updated_registration.to_dict()
        }, 200
        
    except ValueError as e:
        return {
            'data': {
                'code': 'VALIDATION_ERROR',
                'message': str(e),
                'details': None
            }
        }, 400
    except Exception as e:
        current_app.logger.error(f"Update registration error: {str(e)}")
        return {
            'data': {
                'code': 'UPDATE_REGISTRATION_ERROR',
                'message': 'Failed to update registration',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.delete('/registrations/<registration_id>')
@camp_bp.output(SuccessMessageWrapperSchema)
@camp_bp.doc(
    summary='Cancel registration',
    description='Cancel/delete a registration'
)
@token_required
def cancel_registration(registration_id):
    """Cancel registration"""
    try:
        # Verify user owns the camp that owns this registration
        registration = registration_service.get_registration_by_id(registration_id)
        if not registration:
            return {
                'data': {
                    'code': 'REGISTRATION_NOT_FOUND',
                    'message': 'Registration not found',
                    'details': None
                }
            }, 404
        
        # Check if user owns the camp
        user = get_current_user()
        if str(registration.camp.camp_manager_id) != str(user.id):
            return {
                'data': {
                    'code': 'AUTHORIZATION_ERROR',
                    'message': 'Access denied',
                    'details': None
                }
            }, 403
        
        success = registration_service.cancel_registration(registration_id)
        if not success:
            return {
                'data': {
                    'code': 'CANCEL_FAILED',
                    'message': 'Failed to cancel registration',
                    'details': None
                }
            }, 400
        
        return {
            'data': {
                'message': 'Registration cancelled successfully'
            }
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Cancel registration error: {str(e)}")
        return {
            'data': {
                'code': 'CANCEL_REGISTRATION_ERROR',
                'message': 'Failed to cancel registration',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.patch('/registrations/<registration_id>/payment')
@camp_bp.input({
    'type': 'object',
    'properties': {
        'data': {
            'type': 'object',
            'properties': {
                'has_paid': {'type': 'boolean'},
                'payment_method': {'type': 'string'},
                'transaction_id': {'type': 'string'}
            },
            'required': ['has_paid']
        }
    },
    'required': ['data']
})
@camp_bp.output(RegistrationResponseWrapperSchema)
@camp_bp.doc(
    summary='Update payment status',
    description='Mark registration as paid/unpaid'
)
@token_required
def update_payment_status(registration_id, json_data):
    """Update payment status"""
    try:
        # Verify user owns the camp that owns this registration
        registration = registration_service.get_registration_by_id(registration_id)
        if not registration:
            return {
                'data': {
                    'code': 'REGISTRATION_NOT_FOUND',
                    'message': 'Registration not found',
                    'details': None
                }
            }, 404
        
        # Check if user owns the camp
        user = get_current_user()
        if str(registration.camp.camp_manager_id) != str(user.id):
            return {
                'data': {
                    'code': 'AUTHORIZATION_ERROR',
                    'message': 'Access denied',
                    'details': None
                }
            }, 403
        
        payment_data = json_data['data']
        updated_registration = registration_service.update_payment_status(registration_id, payment_data)
        
        return {
            'data': updated_registration.to_dict()
        }, 200
        
    except ValueError as e:
        return {
            'data': {
                'code': 'VALIDATION_ERROR',
                'message': str(e),
                'details': None
            }
        }, 400
    except Exception as e:
        current_app.logger.error(f"Update payment status error: {str(e)}")
        return {
            'data': {
                'code': 'UPDATE_PAYMENT_ERROR',
                'message': 'Failed to update payment status',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.patch('/registrations/<registration_id>/checkin')
@camp_bp.input({
    'type': 'object',
    'properties': {
        'data': {
            'type': 'object',
            'properties': {
                'has_checked_in': {'type': 'boolean'}
            },
            'required': ['has_checked_in']
        }
    },
    'required': ['data']
})
@camp_bp.output(RegistrationResponseWrapperSchema)
@camp_bp.doc(
    summary='Update check-in status',
    description='Mark registration as checked in/out'
)
@token_required
def update_checkin_status(registration_id, json_data):
    """Update check-in status"""
    try:
        # Verify user owns the camp that owns this registration
        registration = registration_service.get_registration_by_id(registration_id)
        if not registration:
            return {
                'data': {
                    'code': 'REGISTRATION_NOT_FOUND',
                    'message': 'Registration not found',
                    'details': None
                }
            }, 404
        
        # Check if user owns the camp
        user = get_current_user()
        if str(registration.camp.camp_manager_id) != str(user.id):
            return {
                'data': {
                    'code': 'AUTHORIZATION_ERROR',
                    'message': 'Access denied',
                    'details': None
                }
            }, 403
        
        checkin_data = json_data['data']
        updated_registration = registration_service.update_checkin_status(registration_id, checkin_data)
        
        return {
            'data': updated_registration.to_dict()
        }, 200
        
    except ValueError as e:
        return {
            'data': {
                'code': 'VALIDATION_ERROR',
                'message': str(e),
                'details': None
            }
        }, 400
    except Exception as e:
        current_app.logger.error(f"Update check-in status error: {str(e)}")
        return {
            'data': {
                'code': 'UPDATE_CHECKIN_ERROR',
                'message': 'Failed to update check-in status',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.put('/registration-links/<link_id>')
@camp_bp.input(RegistrationLinkUpdateRequestSchema)
@camp_bp.output(RegistrationLinkResponseWrapperSchema)
@camp_bp.doc(
    summary='Update registration link',
    description='Update registration link details'
)
@token_required
def update_registration_link(link_id, json_data):
    """Update registration link"""
    try:
        # Verify user owns the camp that owns this registration link
        link = registration_link_service.get_registration_link_by_id(link_id)
        if not link:
            return {
                'data': {
                    'code': 'LINK_NOT_FOUND',
                    'message': 'Registration link not found',
                    'details': None
                }
            }, 404
        
        # Check if user owns the camp
        user = get_current_user()
        if str(link.camp.camp_manager_id) != str(user.id):
            return {
                'data': {
                    'code': 'AUTHORIZATION_ERROR',
                    'message': 'Access denied',
                    'details': None
                }
            }, 403
        
        update_data = json_data['data']
        updated_link = registration_link_service.update_registration_link(link_id, update_data)
        
        return {
            'data': updated_link.to_dict()
        }, 200
        
    except ValueError as e:
        return {
            'data': {
                'code': 'VALIDATION_ERROR',
                'message': str(e),
                'details': None
            }
        }, 400
    except Exception as e:
        current_app.logger.error(f"Update registration link error: {str(e)}")
        return {
            'data': {
                'code': 'UPDATE_LINK_ERROR',
                'message': 'Failed to update registration link',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.delete('/registration-links/<link_id>')
@camp_bp.output(SuccessMessageWrapperSchema)
@camp_bp.doc(
    summary='Delete registration link',
    description='Delete registration link'
)
@token_required
def delete_registration_link(link_id):
    """Delete registration link"""
    try:
        # Verify user owns the camp that owns this registration link
        link = registration_link_service.get_registration_link_by_id(link_id)
        if not link:
            return {
                'data': {
                    'code': 'LINK_NOT_FOUND',
                    'message': 'Registration link not found',
                    'details': None
                }
            }, 404
        
        # Check if user owns the camp
        user = get_current_user()
        if str(link.camp.camp_manager_id) != str(user.id):
            return {
                'data': {
                    'code': 'AUTHORIZATION_ERROR',
                    'message': 'Access denied',
                    'details': None
                }
            }, 403
        
        success = registration_link_service.delete_registration_link(link_id)
        if not success:
            return {
                'data': {
                    'code': 'DELETE_FAILED',
                    'message': 'Failed to delete registration link',
                    'details': None
                }
            }, 400
        
        return {
            'data': {
                'message': 'Registration link deleted successfully'
            }
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Delete registration link error: {str(e)}")
        return {
            'data': {
                'code': 'DELETE_LINK_ERROR',
                'message': 'Failed to delete registration link',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.patch('/registration-links/<link_id>/toggle')
@camp_bp.output(RegistrationLinkResponseWrapperSchema)
@camp_bp.doc(
    summary='Toggle registration link status',
    description='Activate or deactivate registration link'
)
@token_required
def toggle_registration_link(link_id):
    """Toggle registration link active status"""
    try:
        # Verify user owns the camp that owns this registration link
        link = registration_link_service.get_registration_link_by_id(link_id)
        if not link:
            return {
                'data': {
                    'code': 'LINK_NOT_FOUND',
                    'message': 'Registration link not found',
                    'details': None
                }
            }, 404
        
        # Check if user owns the camp
        user = get_current_user()
        if str(link.camp.camp_manager_id) != str(user.id):
            return {
                'data': {
                    'code': 'AUTHORIZATION_ERROR',
                    'message': 'Access denied',
                    'details': None
                }
            }, 403
        
        updated_link = registration_link_service.toggle_registration_link(link_id)
        
        return {
            'data': updated_link.to_dict()
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Toggle registration link error: {str(e)}")
        return {
            'data': {
                'code': 'TOGGLE_LINK_ERROR',
                'message': 'Failed to toggle registration link',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.put('/custom-fields/<field_id>')
@camp_bp.input(CustomFieldUpdateRequestSchema)
@camp_bp.output(CustomFieldResponseWrapperSchema)
@camp_bp.doc(
    summary='Update custom field',
    description='Update custom field details'
)
@token_required
def update_custom_field(field_id, json_data):
    """Update custom field"""
    try:
        # Verify user owns the camp that owns this custom field
        custom_field = custom_field_service.get_custom_field_by_id(field_id)
        if not custom_field:
            return {
                'data': {
                    'code': 'CUSTOM_FIELD_NOT_FOUND',
                    'message': 'Custom field not found',
                    'details': None
                }
            }, 404
        
        # Check if user owns the camp
        user = get_current_user()
        if str(custom_field.camp.camp_manager_id) != str(user.id):
            return {
                'data': {
                    'code': 'AUTHORIZATION_ERROR',
                    'message': 'Access denied',
                    'details': None
                }
            }, 403
        
        update_data = json_data['data']
        updated_field = custom_field_service.update_custom_field(field_id, update_data)
        
        return {
            'data': updated_field.to_dict()
        }, 200
        
    except ValueError as e:
        return {
            'data': {
                'code': 'VALIDATION_ERROR',
                'message': str(e),
                'details': None
            }
        }, 400
    except Exception as e:
        current_app.logger.error(f"Update custom field error: {str(e)}")
        return {
            'data': {
                'code': 'UPDATE_CUSTOM_FIELD_ERROR',
                'message': 'Failed to update custom field',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.delete('/custom-fields/<field_id>')
@camp_bp.output(SuccessMessageWrapperSchema)
@camp_bp.doc(
    summary='Delete custom field',
    description='Delete custom field from camp'
)
@token_required
def delete_custom_field(field_id):
    """Delete custom field"""
    try:
        # Verify user owns the camp that owns this custom field
        custom_field = custom_field_service.get_custom_field_by_id(field_id)
        if not custom_field:
            return {
                'data': {
                    'code': 'CUSTOM_FIELD_NOT_FOUND',
                    'message': 'Custom field not found',
                    'details': None
                }
            }, 404
        
        # Check if user owns the camp
        user = get_current_user()
        if str(custom_field.camp.camp_manager_id) != str(user.id):
            return {
                'data': {
                    'code': 'AUTHORIZATION_ERROR',
                    'message': 'Access denied',
                    'details': None
                }
            }, 403
        
        success = custom_field_service.delete_custom_field(field_id)
        if not success:
            return {
                'data': {
                    'code': 'DELETE_FAILED',
                    'message': 'Failed to delete custom field',
                    'details': None
                }
            }, 400
        
        return {
            'data': {
                'message': 'Custom field deleted successfully'
            }
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Delete custom field error: {str(e)}")
        return {
            'data': {
                'code': 'DELETE_CUSTOM_FIELD_ERROR',
                'message': 'Failed to delete custom field',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.post('')
@camp_bp.input(CampCreateRequestSchema)
@camp_bp.output(CampResponseWrapperSchema, status_code=201)
@camp_bp.doc(
    summary='Create a new camp',
    description='Create a new camp for the authenticated camp manager'
)
@token_required
@role_required('camp_manager')
def create_camp(json_data):
    """Create a new camp"""
    try:
        user = get_current_user()
        camp_data = json_data['data']
        
        # Add camp manager ID to camp data
        camp_data['camp_manager_id'] = str(user.id)
        
        new_camp = camp_service.create_camp(camp_data)
        
        return {
            'data': new_camp.to_dict()
        }, 201
        
    except ValueError as e:
        return {
            'data': {
                'code': 'VALIDATION_ERROR',
                'message': str(e),
                'details': None
            }
        }, 400
    except Exception as e:
        print(e)
        current_app.logger.error(f"Create camp error: {str(e)}")
        return {
            'data': {
                'code': 'CREATE_CAMP_ERROR',
                'message': 'Failed to create camp',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.get('/<camp_id>')
@camp_bp.output(CampResponseWrapperSchema)
@camp_bp.doc(
    summary='Get camp details',
    description='Get details of a specific camp'
)
@token_required
@camp_owner_required()
def get_camp(camp_id):
    """Get camp details"""
    try:
        camp = camp_service.get_camp_by_id(camp_id)
        
        if not camp:
            return {
                'data': {
                    'code': 'CAMP_NOT_FOUND',
                    'message': 'Camp not found',
                    'details': None
                }
            }, 404
        
        return {
            'data': camp.to_dict()
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Get camp error: {str(e)}")
        return {
            'data': {
                'code': 'GET_CAMP_ERROR',
                'message': 'Failed to retrieve camp',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.put('/<camp_id>')
@camp_bp.input(CampUpdateRequestSchema)
@camp_bp.output(CampResponseWrapperSchema)
@camp_bp.doc(
    summary='Update camp',
    description='Update details of a specific camp'
)
@token_required
@camp_owner_required()
def update_camp(camp_id, json_data):
    """Update camp details"""
    try:
        update_data = json_data['data']
        
        updated_camp = camp_service.update_camp(camp_id, update_data)
        
        if not updated_camp:
            return {
                'data': {
                    'code': 'CAMP_NOT_FOUND',
                    'message': 'Camp not found',
                    'details': None
                }
            }, 404
        
        return {
            'data': updated_camp.to_dict()
        }, 200
        
    except ValueError as e:
        return {
            'data': {
                'code': 'VALIDATION_ERROR',
                'message': str(e),
                'details': None
            }
        }, 400
    except Exception as e:
        current_app.logger.error(f"Update camp error: {str(e)}")
        return {
            'data': {
                'code': 'UPDATE_CAMP_ERROR',
                'message': 'Failed to update camp',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.delete('/<camp_id>')
@camp_bp.output(SuccessMessageWrapperSchema)
@camp_bp.doc(
    summary='Delete camp',
    description='Delete a specific camp and all related data'
)
@token_required
@camp_owner_required()
def delete_camp(camp_id):
    """Delete camp"""
    try:
        success = camp_service.delete_camp(camp_id)
        
        if not success:
            return {
                'data': {
                    'code': 'CAMP_NOT_FOUND',
                    'message': 'Camp not found',
                    'details': None
                }
            }, 404
        
        return {
            'data': {
                'message': 'Camp deleted successfully'
            }
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Delete camp error: {str(e)}")
        return {
            'data': {
                'code': 'DELETE_CAMP_ERROR',
                'message': 'Failed to delete camp',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.get('/<camp_id>/stats')
@camp_bp.output(CampStatsResponseWrapperSchema)
@camp_bp.doc(
    summary='Get camp statistics',
    description='Get registration and financial statistics for a camp'
)
@token_required
@camp_owner_required()
def get_camp_stats(camp_id):
    """Get camp statistics"""
    try:
        stats = camp_service.get_camp_stats(camp_id)
        
        if not stats:
            return {
                'data': {
                    'code': 'CAMP_NOT_FOUND',
                    'message': 'Camp not found',
                    'details': None
                }
            }, 404
        
        return {
            'data': stats
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Get camp stats error: {str(e)}")
        return {
            'data': {
                'code': 'GET_STATS_ERROR',
                'message': 'Failed to retrieve camp statistics',
                'details': {'error': str(e)}
            }
        }, 500


# =============================================================================
# CHURCH ROUTES
# =============================================================================

@camp_bp.get('/<camp_id>/churches')
@camp_bp.output(ChurchListResponseWrapperSchema)
@camp_bp.doc(
    summary='Get churches for camp',
    description='Get all churches associated with a camp'
)
@token_required
@camp_owner_required()
def get_churches(camp_id):
    """Get churches for camp"""
    try:
        churches = church_service.get_camp_churches(camp_id)
        
        return {
            'data': [church.to_dict() for church in churches]
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Get churches error: {str(e)}")
        return {
            'data': {
                'code': 'GET_CHURCHES_ERROR',
                'message': 'Failed to retrieve churches',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.post('/<camp_id>/churches')
@camp_bp.input(ChurchCreateRequestSchema)
@camp_bp.output(ChurchResponseWrapperSchema, status_code=201)
@camp_bp.doc(
    summary='Add church to camp',
    description='Add a new church to a camp'
)
@token_required
@camp_owner_required()
def create_church(camp_id, json_data):
    """Add church to camp"""
    try:
        church_data = json_data['data']
        church_data['camp_id'] = camp_id
        
        new_church = church_service.create_church(church_data)
        
        return {
            'data': new_church.to_dict()
        }, 201
        
    except ValueError as e:
        return {
            'data': {
                'code': 'VALIDATION_ERROR',
                'message': str(e),
                'details': None
            }
        }, 400
    except Exception as e:
        current_app.logger.error(f"Create church error: {str(e)}")
        return {
            'data': {
                'code': 'CREATE_CHURCH_ERROR',
                'message': 'Failed to create church',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.put('/churches/<church_id>')
@camp_bp.input(ChurchUpdateRequestSchema)
@camp_bp.output(ChurchResponseWrapperSchema)
@camp_bp.doc(
    summary='Update church',
    description='Update church details'
)
@token_required
def update_church(church_id, json_data):
    """Update church"""
    try:
        # Verify user owns the camp that owns this church
        church = church_service.get_church_by_id(church_id)
        if not church:
            return {
                'data': {
                    'code': 'CHURCH_NOT_FOUND',
                    'message': 'Church not found',
                    'details': None
                }
            }, 404
        
        # Check if user owns the camp
        user = get_current_user()
        if str(church.camp.camp_manager_id) != str(user.id):
            return {
                'data': {
                    'code': 'AUTHORIZATION_ERROR',
                    'message': 'Access denied',
                    'details': None
                }
            }, 403
        
        update_data = json_data['data']
        updated_church = church_service.update_church(church_id, update_data)
        
        return {
            'data': updated_church.to_dict()
        }, 200
        
    except ValueError as e:
        return {
            'data': {
                'code': 'VALIDATION_ERROR',
                'message': str(e),
                'details': None
            }
        }, 400
    except Exception as e:
        current_app.logger.error(f"Update church error: {str(e)}")
        return {
            'data': {
                'code': 'UPDATE_CHURCH_ERROR',
                'message': 'Failed to update church',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.delete('/churches/<church_id>')
@camp_bp.output(SuccessMessageWrapperSchema)
@camp_bp.doc(
    summary='Remove church',
    description='Remove church from camp'
)
@token_required
def delete_church(church_id):
    """Remove church"""
    try:
        # Verify user owns the camp that owns this church
        church = church_service.get_church_by_id(church_id)
        if not church:
            return {
                'data': {
                    'code': 'CHURCH_NOT_FOUND',
                    'message': 'Church not found',
                    'details': None
                }
            }, 404
        
        # Check if user owns the camp
        user = get_current_user()
        if str(church.camp.camp_manager_id) != str(user.id):
            return {
                'data': {
                    'code': 'AUTHORIZATION_ERROR',
                    'message': 'Access denied',
                    'details': None
                }
            }, 403
        
        church_service.delete_church(church_id)
        
        return {
            'data': {
                'message': 'Church removed successfully'
            }
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Delete church error: {str(e)}")
        return {
            'data': {
                'code': 'DELETE_CHURCH_ERROR',
                'message': 'Failed to remove church',
                'details': {'error': str(e)}
            }
        }, 500


# =============================================================================
# CATEGORY ROUTES
# =============================================================================

@camp_bp.get('/<camp_id>/categories')
@camp_bp.output(CategoryListResponseWrapperSchema)
@camp_bp.doc(
    summary='Get categories for camp',
    description='Get all registration categories for a camp'
)
@token_required
@camp_owner_required()
def get_categories(camp_id):
    """Get categories for camp"""
    try:
        categories = category_service.get_camp_categories(camp_id)
        
        return {
            'data': [category.to_dict() for category in categories]
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Get categories error: {str(e)}")
        return {
            'data': {
                'code': 'GET_CATEGORIES_ERROR',
                'message': 'Failed to retrieve categories',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.post('/<camp_id>/categories')
@camp_bp.input(CategoryCreateRequestSchema)
@camp_bp.output(CategoryResponseWrapperSchema, status_code=201)
@camp_bp.doc(
    summary='Create category',
    description='Create a new registration category for a camp'
)
@token_required
@camp_owner_required()
def create_category(camp_id, json_data):
    """Create category"""
    try:
        category_data = json_data['data']
        category_data['camp_id'] = camp_id
        
        new_category = category_service.create_category(category_data)
        
        return {
            'data': new_category.to_dict()
        }, 201
        
    except ValueError as e:
        return {
            'data': {
                'code': 'VALIDATION_ERROR',
                'message': str(e),
                'details': None
            }
        }, 400
    except Exception as e:
        current_app.logger.error(f"Create category error: {str(e)}")
        return {
            'data': {
                'code': 'CREATE_CATEGORY_ERROR',
                'message': 'Failed to create category',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.put('/categories/<category_id>')
@camp_bp.input(CategoryUpdateRequestSchema)
@camp_bp.output(CategoryResponseWrapperSchema)
@camp_bp.doc(
    summary='Update category',
    description='Update category details'
)
@token_required
def update_category(category_id, json_data):
    """Update category"""
    try:
        # Verify user owns the camp that owns this category
        category = category_service.get_category_by_id(category_id)
        if not category:
            return {
                'data': {
                    'code': 'CATEGORY_NOT_FOUND',
                    'message': 'Category not found',
                    'details': None
                }
            }, 404
        
        # Check if user owns the camp
        user = get_current_user()
        if str(category.camp.camp_manager_id) != str(user.id):
            return {
                'data': {
                    'code': 'AUTHORIZATION_ERROR',
                    'message': 'Access denied',
                    'details': None
                }
            }, 403
        
        update_data = json_data['data']
        updated_category = category_service.update_category(category_id, update_data)
        
        return {
            'data': updated_category.to_dict()
        }, 200
        
    except ValueError as e:
        return {
            'data': {
                'code': 'VALIDATION_ERROR',
                'message': str(e),
                'details': None
            }
        }, 400
    except Exception as e:
        current_app.logger.error(f"Update category error: {str(e)}")
        return {
            'data': {
                'code': 'UPDATE_CATEGORY_ERROR',
                'message': 'Failed to update category',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.delete('/categories/<category_id>')
@camp_bp.output(SuccessMessageWrapperSchema)
@camp_bp.doc(
    summary='Delete category',
    description='Delete category from camp'
)
@token_required
def delete_category(category_id):
    """Delete category"""
    try:
        # Verify user owns the camp that owns this category
        category = category_service.get_category_by_id(category_id)
        if not category:
            return {
                'data': {
                    'code': 'CATEGORY_NOT_FOUND',
                    'message': 'Category not found',
                    'details': None
                }
            }, 404
        
        # Check if user owns the camp
        user = get_current_user()
        if str(category.camp.camp_manager_id) != str(user.id):
            return {
                'data': {
                    'code': 'AUTHORIZATION_ERROR',
                    'message': 'Access denied',
                    'details': None
                }
            }, 403
        
        success = category_service.delete_category(category_id)
        if not success:
            return {
                'data': {
                    'code': 'DELETE_FAILED',
                    'message': 'Failed to delete category',
                    'details': None
                }
            }, 400
        
        return {
            'data': {
                'message': 'Category deleted successfully'
            }
        }, 200
        
    except ValueError as e:
        return {
            'data': {
                'code': 'VALIDATION_ERROR',
                'message': str(e),
                'details': None
            }
        }, 400
    except Exception as e:
        current_app.logger.error(f"Delete category error: {str(e)}")
        return {
            'data': {
                'code': 'DELETE_CATEGORY_ERROR',
                'message': 'Failed to delete category',
                'details': {'error': str(e)}
            }
        }, 500

# =============================================================================
# CUSTOM FIELD ROUTES
# =============================================================================

@camp_bp.get('/<camp_id>/custom-fields')
@camp_bp.output(CustomFieldListResponseWrapperSchema)
@camp_bp.doc(
    summary='Get custom fields',
    description='Get all custom fields for a camp'
)
@token_required
@camp_owner_required()
def get_custom_fields(camp_id):
    """Get custom fields for camp"""
    try:
        custom_fields = custom_field_service.get_camp_custom_fields(camp_id)
        
        return {
            'data': [field.to_dict() for field in custom_fields]
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Get custom fields error: {str(e)}")
        return {
            'data': {
                'code': 'GET_CUSTOM_FIELDS_ERROR',
                'message': 'Failed to retrieve custom fields',
                'details': {'error': str(e)}
            }
        }, 500


# =============================================================================
# REGISTRATION LINK ROUTES
# =============================================================================

@camp_bp.get('/<camp_id>/registration-links')
@camp_bp.output(RegistrationLinkListResponseWrapperSchema)
@camp_bp.doc(
    summary='Get registration links',
    description='Get all registration links for a camp'
)
@token_required
@camp_owner_required()
def get_registration_links(camp_id):
    """Get registration links for camp"""
    try:
        links = registration_link_service.get_camp_registration_links(camp_id)
        
        return {
            'data': [link.to_dict() for link in links]
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Get registration links error: {str(e)}")
        return {
            'data': {
                'code': 'GET_LINKS_ERROR',
                'message': 'Failed to retrieve registration links',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.post('/<camp_id>/registration-links')
@camp_bp.input(RegistrationLinkCreateRequestSchema)
@camp_bp.output(RegistrationLinkResponseWrapperSchema, status_code=201)
@camp_bp.doc(
    summary='Create registration link',
    description='Create a new category-specific registration link'
)
@token_required
@camp_owner_required()
def create_registration_link(camp_id, json_data):
    """Create registration link"""
    try:
        user = get_current_user()
        link_data = json_data['data']
        link_data['camp_id'] = camp_id
        link_data['created_by'] = str(user.id)
        
        new_link = registration_link_service.create_registration_link(link_data)
        
        return {
            'data': new_link.to_dict()
        }, 201
        
    except ValueError as e:
        return {
            'data': {
                'code': 'VALIDATION_ERROR',
                'message': str(e),
                'details': None
            }
        }, 400
    except Exception as e:
        current_app.logger.error(f"Create registration link error: {str(e)}")
        return {
            'data': {
                'code': 'CREATE_LINK_ERROR',
                'message': 'Failed to create registration link',
                'details': {'error': str(e)}
            }
        }, 500


# =============================================================================
# REGISTRATION ROUTES (Public & Private)
# =============================================================================

@camp_bp.get('/<camp_id>/register')
@camp_bp.output(RegistrationFormResponseWrapperSchema)
@camp_bp.doc(
    summary='Get general registration form',
    description='Get registration form structure for general access (all categories)'
)
@optional_auth
def get_registration_form(camp_id):
    """Get general registration form structure"""
    try:
        form_data = registration_service.get_registration_form(camp_id)
        
        if not form_data:
            return {
                'data': {
                    'code': 'CAMP_NOT_FOUND',
                    'message': 'Camp not found or registration not available',
                    'details': None
                }
            }, 404
        
        return {
            'data': form_data
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Get registration form error: {str(e)}")
        return {
            'data': {
                'code': 'GET_FORM_ERROR',
                'message': 'Failed to retrieve registration form',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.post('/<camp_id>/register')
@camp_bp.input(RegistrationCreateRequestSchema)
@camp_bp.output(RegistrationResponseWrapperSchema, status_code=201)
@camp_bp.doc(
    summary='Submit general registration',
    description='Submit registration for general access (all categories available)'
)
def submit_registration(camp_id, json_data):
    """Submit general registration"""
    try:
        registration_data = json_data['data']
        registration_data['camp_id'] = camp_id
        
        new_registration = registration_service.create_registration(registration_data)
        
        return {
            'data': new_registration.to_dict()
        }, 201
        
    except ValueError as e:
        return {
            'data': {
                'code': 'VALIDATION_ERROR',
                'message': str(e),
                'details': None
            }
        }, 400
    except Exception as e:
        current_app.logger.error(f"Submit registration error: {str(e)}")
        return {
            'data': {
                'code': 'REGISTRATION_ERROR',
                'message': 'Failed to submit registration',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.get('/<camp_id>/registrations')
@camp_bp.output(RegistrationListResponseWrapperSchema)
@camp_bp.doc(
    summary='Get camp registrations',
    description='Get all registrations for a camp (Manager only)'
)
@token_required
@camp_owner_required()
def get_registrations(camp_id):
    """Get all registrations for camp"""
    try:
        registrations = registration_service.get_camp_registrations(camp_id)
        
        return {
            'data': [reg.to_dict() for reg in registrations]
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Get registrations error: {str(e)}")
        return {
            'data': {
                'code': 'GET_REGISTRATIONS_ERROR',
                'message': 'Failed to retrieve registrations',
                'details': {'error': str(e)}
            }
        }, 500


# Error handlers for the camp blueprint
@camp_bp.errorhandler(400)
def bad_request(error):
    """Handle bad request errors"""
    return {
        'data': {
            'code': 'BAD_REQUEST',
            'message': 'Bad request',
            'details': {'error': str(error)}
        }
    }, 400


@camp_bp.errorhandler(422)
def validation_error(error):
    """Handle validation errors"""
    return {
        'data': {
            'code': 'VALIDATION_ERROR',
            'message': 'Validation failed',
            'details': error.description if hasattr(error, 'description') else {'error': str(error)}
        }
    }, 422


@camp_bp.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    current_app.logger.error(f"Internal error in camp routes: {str(error)}")
    return {
        'data': {
            'code': 'INTERNAL_ERROR',
            'message': 'Internal server error',
            'details': None
        }
    }, 500