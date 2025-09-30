from flask import request, current_app
from apiflask import APIBlueprint
from flask_jwt_extended import jwt_required

from .models import Camp, Church, Category, CustomField, RegistrationLink, Registration, Payment, Pledge
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
    ChurchCreateMultipleRequestSchema,
    
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

    # Payment Schemas
    PaymentCreateRequestSchema,
    PaymentListResponseWrapperSchema,
    PaymentResponseWrapperSchema,
    
    # Financial Schemas
    FinancialRequestWrapperSchema,
    FinancialListResponseWrapperSchema,
    FinancialResponseWrapperSchema,
    
    # Inventory Schemas
    InventoryRequestWrapperSchema,
    InventoryResponseWrapperSchema,
    InventoryListResponseWrapperSchema,
    
    # Purchase Schemas
    PurchaseRequestWrapperSchema,
    PurchaseResponseWrapperSchema,
    PurchaseListResponseWrapperSchema,
    
    # Pledge Schemas
    PledgeRequestWrapperSchema,
    PledgeResponseWrapperSchema,
    PledgeListResponseWrapperSchema,
    PledgeStatusChangeWrapperSchema,
    
    # Check-in Schemas
    CheckedInRequestWrapperSchema,
    RegistrationsQuerySchema,
    
    # Room schemas
    RoomCreateRequestSchema,
    RoomUpdateRequestSchema,
    RoomResponseWrapperSchema,
    RoomListResponseWrapperSchema,
    
    # Room Allocation schemas
    RoomAllocationCreateRequestSchema,
    RoomAllocationUpdateRequestSchema,
    RoomAllocationResponseWrapperSchema,
    RoomAllocationListResponseWrapperSchema,
    
    # Food schemas
    FoodCreateRequestSchema,
    FoodUpdateRequestSchema,
    FoodResponseWrapperSchema,
    FoodListResponseWrapperSchema,
    
    # Food Allocation schemas
    FoodAllocationCreateRequestSchema,
    FoodAllocationResponseWrapperSchema,
    FoodAllocationListResponseWrapperSchema,
    BulkFoodAllocationRequestSchema,

    EmailQrSchema
)
from app._shared.schemas import SuccessMessageWrapperSchema
from .services import CampService, ChurchService, CategoryService, CustomFieldService, RegistrationLinkService, RegistrationService, PaymentService, FinancialService, InventoryService, PurchaseService, PledgeService, RoomService, RoomAllocationService, FoodService, FoodAllocationService
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
payment_service = PaymentService()
financial_service = FinancialService()
inventory_service = InventoryService()
purchase_service = PurchaseService()
pledge_service = PledgeService()
room_service = RoomService()
room_allocation_service = RoomAllocationService()
food_service = FoodService()
food_allocation_service = FoodAllocationService()

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
# @role_required('camp_manager')
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
#@camp_owner_required()
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

        # if str(link.camp.camp_manager_id) != str(user.id):
        #     return {
        #         'data': {
        #             'code': 'AUTHORIZATION_ERROR',
        #             'message': 'Access denied',
        #             'details': None
        #         }
        #     }, 403
        
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
# @token_required
def get_registration(registration_id):
    """Get registration details"""
    try:
        # Verify user owns the camp that owns this registration
        registration = registration_service.get_registration_by_id(registration_id)
        registration_data = registration.to_dict(include_payments=True)
        registration_data["church"] = registration.church.to_dict(
                for_api=False, include_registrations=False
            )
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
        # if str(registration.camp.camp_manager_id) != str(user.id):
        #     return {
        #         'data': {
        #             'code': 'AUTHORIZATION_ERROR',
        #             'message': 'Access denied',
        #             'details': None
        #         }
        #     }, 403
        
        return {
            'data': registration_data
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
        # if str(registration.camp.camp_manager_id) != str(user.id):
        #     return {
        #         'data': {
        #             'code': 'AUTHORIZATION_ERROR',
        #             'message': 'Access denied',
        #             'details': None
        #         }
        #     }, 403
        
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
        # if str(registration.camp.camp_manager_id) != str(user.id):
        #     return {
        #         'data': {
        #             'code': 'AUTHORIZATION_ERROR',
        #             'message': 'Access denied',
        #             'details': None
        #         }
        #     }, 403
        
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
        # if str(registration.camp.camp_manager_id) != str(user.id):
        #     return {
        #         'data': {
        #             'code': 'AUTHORIZATION_ERROR',
        #             'message': 'Access denied',
        #             'details': None
        #         }
        #     }, 403
        
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
@camp_bp.input(CheckedInRequestWrapperSchema)
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
        # if str(registration.camp.camp_manager_id) != str(user.id):
        #     return {
        #         'data': {
        #             'code': 'AUTHORIZATION_ERROR',
        #             'message': 'Access denied',
        #             'details': None
        #         }
        #     }, 403
        
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
        # if str(link.camp.camp_manager_id) != str(user.id):
        #     return {
        #         'data': {
        #             'code': 'AUTHORIZATION_ERROR',
        #             'message': 'Access denied',
        #             'details': None
        #         }
        #     }, 403
        
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
        # if str(link.camp.camp_manager_id) != str(user.id):
        #     return {
        #         'data': {
        #             'code': 'AUTHORIZATION_ERROR',
        #             'message': 'Access denied',
        #             'details': None
        #         }
        #     }, 403
        
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
        # if str(link.camp.camp_manager_id) != str(user.id):
        #     return {
        #         'data': {
        #             'code': 'AUTHORIZATION_ERROR',
        #             'message': 'Access denied',
        #             'details': None
        #         }
        #     }, 403
        
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
        # if str(custom_field.camp.camp_manager_id) != str(user.id):
        #     return {
        #         'data': {
        #             'code': 'AUTHORIZATION_ERROR',
        #             'message': 'Access denied',
        #             'details': None
        #         }
        #     }, 403
        
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
        # if str(custom_field.camp.camp_manager_id) != str(user.id):
        #     return {
        #         'data': {
        #             'code': 'AUTHORIZATION_ERROR',
        #             'message': 'Access denied',
        #             'details': None
        #         }
        #     }, 403
        
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
#@camp_owner_required()
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
#@camp_owner_required()
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
#@camp_owner_required()
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
#@camp_owner_required()
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
#@camp_owner_required()
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
#@camp_owner_required()
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
        

@camp_bp.post('/<camp_id>/multiple-churches')
@camp_bp.input(ChurchCreateMultipleRequestSchema)
@camp_bp.output(ChurchResponseWrapperSchema, status_code=201)
@camp_bp.doc(
    summary='Add churches to camp',
    description='Add multiple churches to a camp'
)
# @token_required
# #@camp_owner_required()
def create_churches(camp_id, json_data):
    """Add churches to camp"""
    try:
        
        church_data = json_data['data']
        for church in church_data:
            church['camp_id'] = camp_id
        
        new_church = church_service.create_churches(church_data)
        
        return {
            'data': [church.to_dict() for church in new_church]
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
        current_app.logger.error(f"Create churches error: {str(e)}")
        return {
            'data': {
                'code': 'CREATE_CHURCHES_ERROR',
                'message': 'Failed to create churches',
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
        # if str(church.camp.camp_manager_id) != str(user.id):
        #     return {
        #         'data': {
        #             'code': 'AUTHORIZATION_ERROR',
        #             'message': 'Access denied',
        #             'details': None
        #         }
        #     }, 403
        
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
        # if str(church.camp.camp_manager_id) != str(user.id):
        #     return {
        #         'data': {
        #             'code': 'AUTHORIZATION_ERROR',
        #             'message': 'Access denied',
        #             'details': None
        #         }
        #     }, 403
        
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
# #@camp_owner_required()
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
#@camp_owner_required()
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
        # if str(category.camp.camp_manager_id) != str(user.id):
        #     return {
        #         'data': {
        #             'code': 'AUTHORIZATION_ERROR',
        #             'message': 'Access denied',
        #             'details': None
        #         }
        #     }, 403
        
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
        # if str(category.camp.camp_manager_id) != str(user.id):
        #     return {
        #         'data': {
        #             'code': 'AUTHORIZATION_ERROR',
        #             'message': 'Access denied',
        #             'details': None
        #         }
        #     }, 403
        
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
# #@camp_owner_required()
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
#@camp_owner_required()
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
#@camp_owner_required()
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
@camp_bp.input(RegistrationsQuerySchema, location='query')
@camp_bp.output(RegistrationListResponseWrapperSchema)
@camp_bp.doc(
    summary='Get camp registrations',
    description='Get all registrations for a camp (Manager only)'
)
@token_required
#@camp_owner_required()
def get_registrations(camp_id, query_data):
    """Get all registrations for camp"""
    try:
        registrations = registration_service.get_camp_registrations(camp_id, **query_data)
        
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


# =============================================================================
# PAYMENT ROUTES
# =============================================================================

@camp_bp.get('/<camp_id>/payments')
# @camp_bp.output(PaymentListResponseWrapperSchema)
@camp_bp.doc(
    summary='Get camp payments',
    description='Get all payments for a camp (Manager only)'
)
@token_required
# #@camp_owner_required()
def get_payments(camp_id):
    """Get all payments for camp"""
    try:
        payments = payment_service.get_payments_by_camp(camp_id)
        return {
            'data': payments
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Get payments error: {str(e)}")
        return {
            'data': {
                'code': 'GET_PAYMENTS_ERROR',
                'message': 'Failed to retrieve payments',
                'details': {'error': str(e)}
            }
        }, 500
    
@camp_bp.post('/<camp_id>/payments')
@camp_bp.input(PaymentCreateRequestSchema)
# @camp_bp.output(PaymentResponseWrapperSchema, status_code=201)
@camp_bp.doc(
    summary='Create payment',
    description='Create a new payment for a camp'
)
@token_required
# #@camp_owner_required()
def create_payment(camp_id, json_data):
    """Create payment"""
    try:
        payment_data = json_data['data']
        payment_data['camp_id'] = camp_id
        payment_data['recorded_by'] = str(get_current_user().id)
        
        new_payments = payment_service.create_payment(payment_data, user_id=str(get_current_user().id))
        
        return {
            'data': new_payments
        }, 201
        
    except Exception as e:
        current_app.logger.error(f"Create payment error: {str(e)}")
        return {
            'data': {
                'code': 'CREATE_PAYMENT_ERROR',
                'message': 'Failed to create payment',
                'details': {'error': str(e)}
            }
        }, 500


# =============================================================================
# FINANCIAL ROUTES
# =============================================================================

@camp_bp.get('/<camp_id>/financials')
@camp_bp.output(FinancialListResponseWrapperSchema)
@camp_bp.doc(
    summary='Get camp financials',
    description='Get all financial records for a camp (Manager only)'
)
@token_required
#@camp_owner_required()
def get_camp_financials(camp_id):
    """Get all financial records for camp"""
    try:
        financials = financial_service.get_financials_by_camp(camp_id)
        
        return {
            'data': financials
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Get financials error: {str(e)}")
        return {
            'data': {
                'code': 'GET_FINANCIALS_ERROR',
                'message': 'Failed to retrieve financial records',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.post('/<camp_id>/financials')
@camp_bp.input(FinancialRequestWrapperSchema)
@camp_bp.output(FinancialResponseWrapperSchema, status_code=201)
@camp_bp.doc(
    summary='Create financial record',
    description='Create a new financial record for a camp'
)
@token_required
#@camp_owner_required()
def create_financial(camp_id, json_data):
    """Create financial record"""
    try:
        financial_data = json_data['data']
        # Ensure recorded_by is captured from authenticated user
        financial_data['recorded_by'] = str(get_current_user().id)
        
        new_financial = financial_service.create_financial(financial_data, camp_id)
        
        # Normalize recorded_by to the user's full name for response consistency (like payments)
        result = new_financial.to_dict()
        result['recorded_by'] = get_current_user().full_name
        
        return {
            'data': result
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
        current_app.logger.error(f"Create financial error: {str(e)}")
        return {
            'data': {
                'code': 'CREATE_FINANCIAL_ERROR',
                'message': 'Failed to create financial record',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.get('/financials/<financial_id>')
@camp_bp.output(FinancialResponseWrapperSchema)
@camp_bp.doc(
    summary='Get financial record details',
    description='Get details of a specific financial record'
)
@token_required
def get_financial(financial_id):
    """Get financial record details"""
    try:
        # Verify user owns the camp that owns this financial record
        financial = financial_service.get_financial_by_id(financial_id)
        if not financial:
            return {
                'data': {
                    'code': 'FINANCIAL_NOT_FOUND',
                    'message': 'Financial record not found',
                    'details': None
                }
            }, 404
        
        # Check if user owns the camp
        user = get_current_user()
        # if str(financial.camp.camp_manager_id) != str(user.id):
        #     return {
        #         'data': {
        #             'code': 'AUTHORIZATION_ERROR',
        #             'message': 'Access denied',
        #             'details': None
        #         }
        #     }, 403
        
        return {
            'data': financial.to_dict()
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Get financial error: {str(e)}")
        return {
            'data': {
                'code': 'GET_FINANCIAL_ERROR',
                'message': 'Failed to retrieve financial record',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.put('/financials/<financial_id>')
@camp_bp.input(FinancialRequestWrapperSchema)
@camp_bp.output(FinancialResponseWrapperSchema)
@camp_bp.doc(
    summary='Update financial record',
    description='Update financial record details'
)
@token_required
def update_financial(financial_id, json_data):
    """Update financial record"""
    try:
        # Verify user owns the camp that owns this financial record
        financial = financial_service.get_financial_by_id(financial_id)
        if not financial:
            return {
                'data': {
                    'code': 'FINANCIAL_NOT_FOUND',
                    'message': 'Financial record not found',
                    'details': None
                }
            }, 404
        
        # Check if user owns the camp
        user = get_current_user()
        # if str(financial.camp.camp_manager_id) != str(user.id):
        #     return {
        #         'data': {
        #             'code': 'AUTHORIZATION_ERROR',
        #             'message': 'Access denied',
        #             'details': None
        #         }
        #     }, 403
        
        update_data = json_data['data']
        updated_financial = financial_service.update_financial(financial_id, update_data)
        
        return {
            'data': updated_financial.to_dict()
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
        current_app.logger.error(f"Update financial error: {str(e)}")
        return {
            'data': {
                'code': 'UPDATE_FINANCIAL_ERROR',
                'message': 'Failed to update financial record',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.delete('/financials/<financial_id>')
@camp_bp.output(SuccessMessageWrapperSchema)
@camp_bp.doc(
    summary='Delete financial record',
    description='Delete/soft delete a financial record'
)
@token_required
def delete_financial(financial_id):
    """Delete financial record"""
    try:
        # Verify user owns the camp that owns this financial record
        financial = financial_service.get_financial_by_id(financial_id)
        if not financial:
            return {
                'data': {
                    'code': 'FINANCIAL_NOT_FOUND',
                    'message': 'Financial record not found',
                    'details': None
                }
            }, 404
        
        # Check if user owns the camp
        user = get_current_user()
        # if str(financial.camp.camp_manager_id) != str(user.id):
        #     return {
        #         'data': {
        #             'code': 'AUTHORIZATION_ERROR',
        #             'message': 'Access denied',
        #             'details': None
        #         }
        #     }, 403
        
        success = financial_service.delete_financial(financial_id)
        if not success:
            return {
                'data': {
                    'code': 'DELETE_FAILED',
                    'message': 'Failed to delete financial record',
                    'details': None
                }
            }, 400
        
        return {
            'data': {
                'message': 'Financial record deleted successfully'
            }
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Delete financial error: {str(e)}")
        return {
            'data': {
                'code': 'DELETE_FINANCIAL_ERROR',
                'message': 'Failed to delete financial record',
                'details': {'error': str(e)}
            }
        }, 500


# =============================================================================
# INVENTORY ROUTES
# =============================================================================

@camp_bp.get('/<camp_id>/inventory')
@camp_bp.output(InventoryListResponseWrapperSchema)
@camp_bp.doc(
    summary='Get camp inventory',
    description='Get all inventory items for a camp (Manager only)'
)
@token_required
# #@camp_owner_required()
def get_camp_inventory(camp_id):
    """Get all inventory items for camp"""
    try:
        inventory_items = inventory_service.get_inventory_by_camp(camp_id)
        
        return {
            'data': [item.to_dict() for item in inventory_items]
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Get inventory error: {str(e)}")
        return {
            'data': {
                'code': 'GET_INVENTORY_ERROR',
                'message': 'Failed to retrieve inventory items',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.post('/<camp_id>/inventory')
@camp_bp.input(InventoryRequestWrapperSchema)
@camp_bp.output(InventoryResponseWrapperSchema, status_code=201)
@camp_bp.doc(
    summary='Create inventory item',
    description='Create a new inventory item for a camp'
)
@token_required
# #@camp_owner_required()
def create_inventory_item(camp_id, json_data):
    """Create inventory item"""
    try:
        inventory_data = json_data['data']
        inventory_data['camp_id'] = camp_id
        
        new_inventory = inventory_service.create_inventory(inventory_data)
        
        return {
            'data': new_inventory.to_dict()
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
        current_app.logger.error(f"Create inventory error: {str(e)}")
        return {
            'data': {
                'code': 'CREATE_INVENTORY_ERROR',
                'message': 'Failed to create inventory item',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.get('/inventory/<inventory_id>')
@camp_bp.output(InventoryResponseWrapperSchema)
@camp_bp.doc(
    summary='Get inventory item details',
    description='Get details of a specific inventory item'
)
@token_required
def get_inventory_item(inventory_id):
    """Get inventory item details"""
    try:
        # Get camp_id from query params or determine from inventory item
        camp_id = request.args.get('camp_id')
        if not camp_id:
            return {
                'data': {
                    'code': 'MISSING_CAMP_ID',
                    'message': 'Camp ID is required',
                    'details': None
                }
            }, 400
        
        inventory_item = inventory_service.get_inventory_by_id(inventory_id, camp_id)
        if not inventory_item:
            return {
                'data': {
                    'code': 'INVENTORY_NOT_FOUND',
                    'message': 'Inventory item not found',
                    'details': None
                }
            }, 404
        
        return {
            'data': inventory_item.to_dict()
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Get inventory item error: {str(e)}")
        return {
            'data': {
                'code': 'GET_INVENTORY_ITEM_ERROR',
                'message': 'Failed to retrieve inventory item',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.put('/inventory/<inventory_id>')
@camp_bp.input(InventoryRequestWrapperSchema)
@camp_bp.output(InventoryResponseWrapperSchema)
@camp_bp.doc(
    summary='Update inventory item',
    description='Update inventory item details'
)
@token_required
def update_inventory_item(inventory_id, json_data):
    """Update inventory item"""
    try:
        update_data = json_data['data']
        camp_id = update_data.get('camp_id')
        
        if not camp_id:
            return {
                'data': {
                    'code': 'MISSING_CAMP_ID',
                    'message': 'Camp ID is required',
                    'details': None
                }
            }, 400
        
        updated_inventory = inventory_service.update_inventory(inventory_id, update_data, camp_id)
        
        if not updated_inventory:
            return {
                'data': {
                    'code': 'INVENTORY_NOT_FOUND',
                    'message': 'Inventory item not found',
                    'details': None
                }
            }, 404
        
        return {
            'data': updated_inventory.to_dict()
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
        current_app.logger.error(f"Update inventory item error: {str(e)}")
        return {
            'data': {
                'code': 'UPDATE_INVENTORY_ERROR',
                'message': 'Failed to update inventory item',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.delete('/inventory/<inventory_id>')
@camp_bp.output(SuccessMessageWrapperSchema)
@camp_bp.doc(
    summary='Delete inventory item',
    description='Delete/soft delete an inventory item'
)
@token_required
def delete_inventory_item(inventory_id):
    """Delete inventory item"""
    try:
        camp_id = request.args.get('camp_id')
        if not camp_id:
            return {
                'data': {
                    'code': 'MISSING_CAMP_ID',
                    'message': 'Camp ID is required',
                    'details': None
                }
            }, 400
        
        success = inventory_service.delete_inventory(inventory_id, camp_id)
        if not success:
            return {
                'data': {
                    'code': 'DELETE_FAILED',
                    'message': 'Failed to delete inventory item',
                    'details': None
                }
            }, 400
        
        return {
            'data': {
                'message': 'Inventory item deleted successfully'
            }
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Delete inventory item error: {str(e)}")
        return {
            'data': {
                'code': 'DELETE_INVENTORY_ERROR',
                'message': 'Failed to delete inventory item',
                'details': {'error': str(e)}
            }
        }, 500


# =============================================================================
# PURCHASE ROUTES
# =============================================================================

@camp_bp.get('/<camp_id>/purchases')
@camp_bp.output(PurchaseListResponseWrapperSchema)
@camp_bp.doc(
    summary='Get camp purchases',
    description='Get all purchase records for a camp (Manager only)'
)
@token_required
# #@camp_owner_required()
def get_camp_purchases(camp_id):
    """Get all purchase records for camp"""
    try:
        purchases = purchase_service.get_purchases_by_camp(camp_id)
        
        return {
            'data': [purchase.to_dict() for purchase in purchases]
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Get purchases error: {str(e)}")
        return {
            'data': {
                'code': 'GET_PURCHASES_ERROR',
                'message': 'Failed to retrieve purchase records',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.post('/<camp_id>/purchases')
@camp_bp.input(PurchaseRequestWrapperSchema)
@camp_bp.output(PurchaseResponseWrapperSchema, status_code=201)
@camp_bp.doc(
    summary='Create purchase record',
    description='Create a new purchase record for a camp'
)
@token_required
# #@camp_owner_required()
def create_purchase(camp_id, json_data):
    """Create purchase record"""
    try:
        purchase_data = json_data['data']
        purchase_data['camp_id'] = camp_id
        purchase_data['sold_by'] = str(get_current_user().id)
        
        new_purchase = purchase_service.create_purchase(purchase_data)
        
        return {
            'data': new_purchase.to_dict()
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
        current_app.logger.error(f"Create purchase error: {str(e)}")
        return {
            'data': {
                'code': 'CREATE_PURCHASE_ERROR',
                'message': 'Failed to create purchase record',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.get('/purchases/<purchase_id>')
@camp_bp.output(PurchaseResponseWrapperSchema)
@camp_bp.doc(
    summary='Get purchase record details',
    description='Get details of a specific purchase record'
)
@token_required
def get_purchase(purchase_id):
    """Get purchase record details"""
    try:
        camp_id = request.args.get('camp_id')
        if not camp_id:
            return {
                'data': {
                    'code': 'MISSING_CAMP_ID',
                    'message': 'Camp ID is required',
                    'details': None
                }
            }, 400
        
        purchase = purchase_service.get_purchase_by_id(purchase_id, camp_id)
        if not purchase:
            return {
                'data': {
                    'code': 'PURCHASE_NOT_FOUND',
                    'message': 'Purchase record not found',
                    'details': None
                }
            }, 404
        
        return {
            'data': purchase.to_dict()
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Get purchase error: {str(e)}")
        return {
            'data': {
                'code': 'GET_PURCHASE_ERROR',
                'message': 'Failed to retrieve purchase record',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.put('/purchases/<purchase_id>')
@camp_bp.input(PurchaseRequestWrapperSchema)
@camp_bp.output(PurchaseResponseWrapperSchema)
@camp_bp.doc(
    summary='Update purchase record',
    description='Update purchase record details'
)
@token_required
def update_purchase(purchase_id, json_data):
    """Update purchase record"""
    try:
        update_data = json_data['data']
        camp_id = update_data.get('camp_id')
        
        if not camp_id:
            return {
                'data': {
                    'code': 'MISSING_CAMP_ID',
                    'message': 'Camp ID is required',
                    'details': None
                }
            }, 400
        
        updated_purchase = purchase_service.update_purchase(purchase_id, update_data, camp_id)
        
        if not updated_purchase:
            return {
                'data': {
                    'code': 'PURCHASE_NOT_FOUND',
                    'message': 'Purchase record not found',
                    'details': None
                }
            }, 404
        
        return {
            'data': updated_purchase.to_dict()
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
        current_app.logger.error(f"Update purchase error: {str(e)}")
        return {
            'data': {
                'code': 'UPDATE_PURCHASE_ERROR',
                'message': 'Failed to update purchase record',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.delete('/purchases/<purchase_id>')
@camp_bp.output(SuccessMessageWrapperSchema)
@camp_bp.doc(
    summary='Delete purchase record',
    description='Delete a purchase record'
)
@token_required
def delete_purchase(purchase_id):
    """Delete purchase record"""
    try:
        camp_id = request.args.get('camp_id')
        if not camp_id:
            return {
                'data': {
                    'code': 'MISSING_CAMP_ID',
                    'message': 'Camp ID is required',
                    'details': None
                }
            }, 400
        
        success = purchase_service.delete_purchase(purchase_id, camp_id)
        if not success:
            return {
                'data': {
                    'code': 'DELETE_FAILED',
                    'message': 'Failed to delete purchase record',
                    'details': None
                }
            }, 400
        
        return {
            'data': {
                'message': 'Purchase record deleted successfully'
            }
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Delete purchase error: {str(e)}")
        return {
            'data': {
                'code': 'DELETE_PURCHASE_ERROR',
                'message': 'Failed to delete purchase record',
                'details': {'error': str(e)}
            }
        }, 500


# =============================================================================
# PLEDGE ROUTES
# =============================================================================

@camp_bp.get('/<camp_id>/pledges')
@camp_bp.output(PledgeListResponseWrapperSchema)
@camp_bp.doc(
    summary='Get camp pledges',
    description='Get all pledge records for a camp (Manager only)'
)
@token_required
# #@camp_owner_required()
def get_camp_pledges(camp_id):
    """Get all pledge records for camp"""
    try:
        pledges = pledge_service.get_pledges_by_camp(camp_id)
        pledge_data = [pledge.to_dict() for pledge in pledges]
        for pledge in pledge_data:
            camper = Registration.query.get(pledge['camper_id'])
            if camper:
                pledge['camper_name'] = camper.last_name + ', ' + camper.surname
                pledge['camper_code'] = camper.camper_code
            
        
        return {
            'data': pledge_data
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Get pledges error: {str(e)}")
        return {
            'data': {
                'code': 'GET_PLEDGES_ERROR',
                'message': 'Failed to retrieve pledge records',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.post('/<camp_id>/pledges')
@camp_bp.input(PledgeRequestWrapperSchema)
@camp_bp.output(PledgeResponseWrapperSchema, status_code=201)
@camp_bp.doc(
    summary='Create pledge record',
    description='Create a new pledge record for a camp'
)
@token_required
# #@camp_owner_required()
def create_pledge(camp_id, json_data):
    """Create pledge record"""
    try:
        pledge_data = json_data['data']
        pledge_data['camp_id'] = camp_id
        
        new_pledge = pledge_service.create_pledge(pledge_data)
        
        return {
            'data': new_pledge.to_dict()
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
        current_app.logger.error(f"Create pledge error: {str(e)}")
        return {
            'data': {
                'code': 'CREATE_PLEDGE_ERROR',
                'message': 'Failed to create pledge record',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.get('/pledges/<pledge_id>')
@camp_bp.output(PledgeResponseWrapperSchema)
@camp_bp.doc(
    summary='Get pledge record details',
    description='Get details of a specific pledge record'
)
@token_required
def get_pledge(pledge_id):
    """Get pledge record details"""
    try:
        camp_id = request.args.get('camp_id')
        if not camp_id:
            return {
                'data': {
                    'code': 'MISSING_CAMP_ID',
                    'message': 'Camp ID is required',
                    'details': None
                }
            }, 400
        
        pledge = pledge_service.get_pledge_by_id(pledge_id, camp_id)
        if not pledge:
            return {
                'data': {
                    'code': 'PLEDGE_NOT_FOUND',
                    'message': 'Pledge record not found',
                    'details': None
                }
            }, 404
        
        return {
            'data': pledge.to_dict()
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Get pledge error: {str(e)}")
        return {
            'data': {
                'code': 'GET_PLEDGE_ERROR',
                'message': 'Failed to retrieve pledge record',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.put('/pledges/<pledge_id>')
@camp_bp.input(PledgeRequestWrapperSchema)
@camp_bp.output(PledgeResponseWrapperSchema)
@camp_bp.doc(
    summary='Update pledge record',
    description='Update pledge record details'
)
@token_required
def update_pledge(pledge_id, json_data):
    """Update pledge record"""
    try:
        update_data = json_data['data']
        camp_id = update_data.get('camp_id')
        
        if not camp_id:
            return {
                'data': {
                    'code': 'MISSING_CAMP_ID',
                    'message': 'Camp ID is required',
                    'details': None
                }
            }, 400
        
        updated_pledge = pledge_service.update_pledge(pledge_id, update_data, camp_id)
        
        if not updated_pledge:
            return {
                'data': {
                    'code': 'PLEDGE_NOT_FOUND',
                    'message': 'Pledge record not found',
                    'details': None
                }
            }, 404
        
        return {
            'data': updated_pledge.to_dict()
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
        current_app.logger.error(f"Update pledge error: {str(e)}")
        return {
            'data': {
                'code': 'UPDATE_PLEDGE_ERROR',
                'message': 'Failed to update pledge record',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.delete('/pledges/<pledge_id>')
@camp_bp.output(SuccessMessageWrapperSchema)
@camp_bp.doc(
    summary='Delete pledge record',
    description='Delete a pledge record'
)
@token_required
def delete_pledge(pledge_id):
    """Delete pledge record"""
    try:
        camp_id = request.args.get('camp_id')
        if not camp_id:
            return {
                'data': {
                    'code': 'MISSING_CAMP_ID',
                    'message': 'Camp ID is required',
                    'details': None
                }
            }, 400
        
        success = pledge_service.delete_pledge(pledge_id, camp_id)
        if not success:
            return {
                'data': {
                    'code': 'DELETE_FAILED',
                    'message': 'Failed to delete pledge record',
                    'details': None
                }
            }, 400
        
        return {
            'data': {
                'message': 'Pledge record deleted successfully'
            }
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Delete pledge error: {str(e)}")
        return {
            'data': {
                'code': 'DELETE_PLEDGE_ERROR',
                'message': 'Failed to delete pledge record',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.get('/<camp_id>/pledges/stats')
@camp_bp.output({
    'type': 'object',
    'properties': {
        'data': {
            'type': 'object',
            'properties': {
                'total_pledges': {'type': 'integer'},
                'total_amount': {'type': 'number'},
                'pending_pledges': {'type': 'integer'},
                'pending_amount': {'type': 'number'},
                'fulfilled_pledges': {'type': 'integer'},
                'fulfilled_amount': {'type': 'number'},
                'cancelled_pledges': {'type': 'integer'},
                'cancelled_amount': {'type': 'number'},
                'fulfillment_rate': {'type': 'number'}
            }
        }
    }
})
@camp_bp.doc(
    summary='Get pledge statistics',
    description='Get pledge statistics for a camp (Manager only)'
)
@token_required
# #@camp_owner_required()
def get_pledge_stats(camp_id):
    """Get pledge statistics for camp"""
    try:
        stats = pledge_service.get_camp_pledge_stats(camp_id)
        
        return {
            'data': stats
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Get pledge stats error: {str(e)}")
        return {
            'data': {
                'code': 'GET_PLEDGE_STATS_ERROR',
                'message': 'Failed to retrieve pledge statistics',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.get('/registrations/<registration_id>/pledges')
@camp_bp.output(PledgeListResponseWrapperSchema)
@camp_bp.doc(
    summary='Get camper pledges',
    description='Get all pledges for a specific camper'
)
@token_required
def get_camper_pledges(registration_id):
    """Get all pledges for a specific camper"""
    try:
        camp_id = request.args.get('camp_id')
        if not camp_id:
            return {
                'data': {
                    'code': 'MISSING_CAMP_ID',
                    'message': 'Camp ID is required',
                    'details': None
                }
            }, 400
        
        pledges = pledge_service.get_pledges_by_camper(registration_id, camp_id)
        
        return {
            'data': [pledge.to_dict() for pledge in pledges]
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Get camper pledges error: {str(e)}")
        return {
            'data': {
                'code': 'GET_CAMPER_PLEDGES_ERROR',
                'message': 'Failed to retrieve camper pledges',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.patch('/pledges/<pledge_id>/status')
@camp_bp.input(PledgeStatusChangeWrapperSchema)
@camp_bp.output(PledgeResponseWrapperSchema)
@camp_bp.doc(
    summary='Change pledge status',
    description='Change the status of a pledge between pending, fulfilled, and cancelled'
)
@token_required
def change_pledge_status(pledge_id, json_data):
    """Change pledge status"""
    try:
        # camp_id = request.args.get('camp_id')
        # if not camp_id:
        #     return {
        #         'data': {
        #             'code': 'MISSING_CAMP_ID',
        #             'message': 'Camp ID is required',
        #             'details': None
        #         }
        #     }, 400
        
        status_data = json_data['data']
        new_status = status_data['status']
        camp_id = status_data.get('camp_id')
        
        updated_pledge = pledge_service.change_pledge_status(pledge_id, new_status, camp_id)
        
        if not updated_pledge:
            return {
                'data': {
                    'code': 'PLEDGE_NOT_FOUND',
                    'message': 'Pledge record not found',
                    'details': None
                }
            }, 404
        
        # Get camper information for response
        pledge_data = updated_pledge.to_dict()
        camper = Registration.query.get(updated_pledge.camper_id)
        if camper:
            pledge_data['camper_name'] = camper.last_name + ', ' + camper.surname
            pledge_data['camper_code'] = camper.camper_code
        
        return {
            'data': pledge_data
        }, 200
        
    except ValueError as e:
        print(e)
        return {
            'data': {
                'code': 'VALIDATION_ERROR',
                'message': str(e),
                'details': None
            }
        }, 400
    except Exception as e:
        current_app.logger.error(f"Change pledge status error: {str(e)}")
        return {
            'data': {
                'code': 'CHANGE_PLEDGE_STATUS_ERROR',
                'message': 'Failed to change pledge status',
                'details': {'error': str(e)}
            }
        }, 500


# =============================================================================
# ROOM ROUTES
# =============================================================================

@camp_bp.get('/<camp_id>/rooms')
@camp_bp.output(RoomListResponseWrapperSchema)
@camp_bp.doc(
    summary='Get camp rooms',
    description='Get all rooms for a camp (Manager only)'
)
@token_required
#@camp_owner_required()
def get_camp_rooms(camp_id):
    """Get all rooms for camp"""
    try:
        rooms = room_service.get_camp_rooms(camp_id)
        
        return {
            'data': [room.to_dict() for room in rooms]
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Get rooms error: {str(e)}")
        return {
            'data': {
                'code': 'GET_ROOMS_ERROR',
                'message': 'Failed to retrieve rooms',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.post('/<camp_id>/rooms')
@camp_bp.input(RoomCreateRequestSchema)
@camp_bp.output(RoomResponseWrapperSchema, status_code=201)
@camp_bp.doc(
    summary='Create room',
    description='Create a new room for a camp'
)
@token_required
#@camp_owner_required()
def create_room(camp_id, json_data):
    """Create room"""
    try:
        room_data = json_data['data']
        room_data['camp_id'] = camp_id
        
        new_room = room_service.create_room(room_data)
        
        return {
            'data': new_room.to_dict()
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
        current_app.logger.error(f"Create room error: {str(e)}")
        return {
            'data': {
                'code': 'CREATE_ROOM_ERROR',
                'message': 'Failed to create room',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.get('/rooms/<room_id>')
@camp_bp.output(RoomResponseWrapperSchema)
@camp_bp.doc(
    summary='Get room details',
    description='Get details of a specific room'
)
@token_required
def get_room(room_id):
    """Get room details"""
    try:
        room = room_service.get_room_by_id(room_id)
        if not room:
            return {
                'data': {
                    'code': 'ROOM_NOT_FOUND',
                    'message': 'Room not found',
                    'details': None
                }
            }, 404
        
        # Check if user owns the camp
        user = get_current_user()
        # Add authorization check if needed
        
        return {
            'data': room.to_dict()
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Get room error: {str(e)}")
        return {
            'data': {
                'code': 'GET_ROOM_ERROR',
                'message': 'Failed to retrieve room',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.put('/rooms/<room_id>')
@camp_bp.input(RoomUpdateRequestSchema)
@camp_bp.output(RoomResponseWrapperSchema)
@camp_bp.doc(
    summary='Update room',
    description='Update room details'
)
@token_required
def update_room(room_id, json_data):
    """Update room"""
    try:
        room = room_service.get_room_by_id(room_id)
        if not room:
            return {
                'data': {
                    'code': 'ROOM_NOT_FOUND',
                    'message': 'Room not found',
                    'details': None
                }
            }, 404
        
        # Check if user owns the camp
        user = get_current_user()
        # Add authorization check if needed
        
        update_data = json_data['data']
        updated_room = room_service.update_room(room_id, update_data)
        
        return {
            'data': updated_room.to_dict()
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
        current_app.logger.error(f"Update room error: {str(e)}")
        return {
            'data': {
                'code': 'UPDATE_ROOM_ERROR',
                'message': 'Failed to update room',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.delete('/rooms/<room_id>')
@camp_bp.output(SuccessMessageWrapperSchema)
@camp_bp.doc(
    summary='Delete room',
    description='Delete a room'
)
@token_required
def delete_room(room_id):
    """Delete room"""
    try:
        room = room_service.get_room_by_id(room_id)
        if not room:
            return {
                'data': {
                    'code': 'ROOM_NOT_FOUND',
                    'message': 'Room not found',
                    'details': None
                }
            }, 404
        
        # Check if user owns the camp
        user = get_current_user()
        # Add authorization check if needed
        
        success = room_service.delete_room(room_id)
        if not success:
            return {
                'data': {
                    'code': 'DELETE_FAILED',
                    'message': 'Failed to delete room',
                    'details': None
                }
            }, 400
        
        return {
            'data': {
                'message': 'Room deleted successfully'
            }
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Delete room error: {str(e)}")
        return {
            'data': {
                'code': 'DELETE_ROOM_ERROR',
                'message': 'Failed to delete room',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.get('/<camp_id>/rooms/available')
@camp_bp.output(RoomListResponseWrapperSchema)
@camp_bp.doc(
    summary='Get available rooms',
    description='Get all available rooms for a camp with optional gender filter'
)
@token_required
#@camp_owner_required()
def get_available_rooms(camp_id):
    """Get available rooms for camp"""
    try:
        gender = request.args.get('gender')
        rooms = room_service.get_available_rooms(camp_id, gender)
        
        return {
            'data': [room.to_dict() for room in rooms]
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Get available rooms error: {str(e)}")
        return {
            'data': {
                'code': 'GET_AVAILABLE_ROOMS_ERROR',
                'message': 'Failed to retrieve available rooms',
                'details': {'error': str(e)}
            }
        }, 500


# =============================================================================
# ROOM ALLOCATION ROUTES
# =============================================================================

@camp_bp.get('/<camp_id>/room-allocations')
@camp_bp.output(RoomAllocationListResponseWrapperSchema)
@camp_bp.doc(
    summary='Get camp room allocations',
    description='Get all room allocations for a camp (Manager only)'
)
@token_required
#@camp_owner_required()
def get_camp_room_allocations(camp_id):
    """Get all room allocations for camp"""
    try:
        allocations = room_allocation_service.get_camp_allocations(camp_id)
        
        return {
            'data': [allocation.to_dict(include_details=True) for allocation in allocations]
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Get room allocations error: {str(e)}")
        return {
            'data': {
                'code': 'GET_ROOM_ALLOCATIONS_ERROR',
                'message': 'Failed to retrieve room allocations',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.post('/<camp_id>/room-allocations')
@camp_bp.input(RoomAllocationCreateRequestSchema)
@camp_bp.output(RoomAllocationResponseWrapperSchema, status_code=201)
@camp_bp.doc(
    summary='Allocate room',
    description='Allocate a room to a camper registration'
)
@token_required
#@camp_owner_required()
def allocate_room(camp_id, json_data):
    """Allocate room to camper"""
    try:
        allocation_data = json_data['data']
        allocation_data['camp_id'] = camp_id
        
        new_allocations = room_allocation_service.allocate_room(allocation_data, get_current_user().id)
        
        return {
            'data': [allocation.to_dict() for allocation in new_allocations]
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
        current_app.logger.error(f"Allocate room error: {str(e)}")
        return {
            'data': {
                'code': 'ALLOCATE_ROOM_ERROR',
                'message': 'Failed to allocate room',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.get('/room-allocations/<allocation_id>')
@camp_bp.output(RoomAllocationResponseWrapperSchema)
@camp_bp.doc(
    summary='Get room allocation details',
    description='Get details of a specific room allocation'
)
@token_required
def get_room_allocation(allocation_id):
    """Get room allocation details"""
    try:
        allocation = room_allocation_service.get_allocation_by_id(allocation_id)
        if not allocation:
            return {
                'data': {
                    'code': 'ALLOCATION_NOT_FOUND',
                    'message': 'Room allocation not found',
                    'details': None
                }
            }, 404
        
        # Check if user owns the camp
        user = get_current_user()
        # Add authorization check if needed
        
        return {
            'data': allocation.to_dict()
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Get room allocation error: {str(e)}")
        return {
            'data': {
                'code': 'GET_ROOM_ALLOCATION_ERROR',
                'message': 'Failed to retrieve room allocation',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.put('/room-allocations/<allocation_id>')
@camp_bp.input(RoomAllocationUpdateRequestSchema)
@camp_bp.output(RoomAllocationResponseWrapperSchema)
@camp_bp.doc(
    summary='Update room allocation',
    description='Update room allocation details'
)
@token_required
def update_room_allocation(allocation_id, json_data):
    """Update room allocation"""
    try:
        allocation = room_allocation_service.get_allocation_by_id(allocation_id)
        if not allocation:
            return {
                'data': {
                    'code': 'ALLOCATION_NOT_FOUND',
                    'message': 'Room allocation not found',
                    'details': None
                }
            }, 404
        
        # Check if user owns the camp
        user = get_current_user()
        # Add authorization check if needed
        
        update_data = json_data['data']
        updated_allocation = room_allocation_service.update_allocation(allocation_id, update_data)
        
        return {
            'data': updated_allocation.to_dict()
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
        current_app.logger.error(f"Update room allocation error: {str(e)}")
        return {
            'data': {
                'code': 'UPDATE_ROOM_ALLOCATION_ERROR',
                'message': 'Failed to update room allocation',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.delete('/room-allocations/<allocation_id>')
@camp_bp.output(SuccessMessageWrapperSchema)
@camp_bp.doc(
    summary='Deallocate room',
    description='Remove room allocation for a camper'
)
@token_required
def deallocate_room(allocation_id):
    """Deallocate room from camper"""
    try:
        allocation = room_allocation_service.get_allocation_by_id(allocation_id)
        if not allocation:
            return {
                'data': {
                    'code': 'ALLOCATION_NOT_FOUND',
                    'message': 'Room allocation not found',
                    'details': None
                }
            }, 404
        
        # Check if user owns the camp
        user = get_current_user()
        # Add authorization check if needed
        
        success = room_allocation_service.deallocate_room(allocation_id)
        if not success:
            return {
                'data': {
                    'code': 'DEALLOCATE_FAILED',
                    'message': 'Failed to deallocate room',
                    'details': None
                }
            }, 400
        
        return {
            'data': {
                'message': 'Room deallocated successfully'
            }
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Deallocate room error: {str(e)}")
        return {
            'data': {
                'code': 'DEALLOCATE_ROOM_ERROR',
                'message': 'Failed to deallocate room',
                'details': {'error': str(e)}
            }
        }, 500


# =============================================================================
# FOOD ROUTES
# =============================================================================

@camp_bp.get('/<camp_id>/foods')
@camp_bp.output(FoodListResponseWrapperSchema)
@camp_bp.doc(
    summary='Get camp foods',
    description='Get all food items for a camp (Manager only)'
)
@token_required
#@camp_owner_required()
def get_camp_foods(camp_id):
    """Get all food items for camp"""
    try:
        category = request.args.get('category')
        date_str = request.args.get('date')
        date = None
        if date_str:
            from datetime import datetime
            date = datetime.fromisoformat(date_str)
        
        foods = food_service.get_camp_foods(camp_id, category, date)
        
        return {
            'data': [food.to_dict() for food in foods]
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Get foods error: {str(e)}")
        return {
            'data': {
                'code': 'GET_FOODS_ERROR',
                'message': 'Failed to retrieve food items',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.post('/<camp_id>/foods')
@camp_bp.input(FoodCreateRequestSchema)
@camp_bp.output(FoodResponseWrapperSchema, status_code=201)
@camp_bp.doc(
    summary='Create food item',
    description='Create a new food item for a camp'
)
@token_required
#@camp_owner_required()
def create_food(camp_id, json_data):
    """Create food item"""
    try:
        food_data = json_data['data']
        food_data['camp_id'] = camp_id
        
        new_food = food_service.create_food(food_data)
        
        return {
            'data': new_food.to_dict()
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
        current_app.logger.error(f"Create food error: {str(e)}")
        return {
            'data': {
                'code': 'CREATE_FOOD_ERROR',
                'message': 'Failed to create food item',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.get('/foods/<food_id>')
@camp_bp.output(FoodResponseWrapperSchema)
@camp_bp.doc(
    summary='Get food details',
    description='Get details of a specific food item'
)
@token_required
def get_food(food_id):
    """Get food details"""
    try:
        food = food_service.get_food_by_id(food_id)
        if not food:
            return {
                'data': {
                    'code': 'FOOD_NOT_FOUND',
                    'message': 'Food item not found',
                    'details': None
                }
            }, 404
        
        # Check if user owns the camp
        user = get_current_user()
        # Add authorization check if needed
        
        return {
            'data': food.to_dict()
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Get food error: {str(e)}")
        return {
            'data': {
                'code': 'GET_FOOD_ERROR',
                'message': 'Failed to retrieve food item',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.put('/foods/<food_id>')
@camp_bp.input(FoodUpdateRequestSchema)
@camp_bp.output(FoodResponseWrapperSchema)
@camp_bp.doc(
    summary='Update food item',
    description='Update food item details'
)
@token_required
def update_food(food_id, json_data):
    """Update food item"""
    try:
        food = food_service.get_food_by_id(food_id)
        if not food:
            return {
                'data': {
                    'code': 'FOOD_NOT_FOUND',
                    'message': 'Food item not found',
                    'details': None
                }
            }, 404
        
        # Check if user owns the camp
        user = get_current_user()
        # Add authorization check if needed
        
        update_data = json_data['data']
        updated_food = food_service.update_food(food_id, update_data)
        
        return {
            'data': updated_food.to_dict()
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
        current_app.logger.error(f"Update food error: {str(e)}")
        return {
            'data': {
                'code': 'UPDATE_FOOD_ERROR',
                'message': 'Failed to update food item',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.delete('/foods/<food_id>')
@camp_bp.output(SuccessMessageWrapperSchema)
@camp_bp.doc(
    summary='Delete food item',
    description='Delete a food item'
)
@token_required
def delete_food(food_id):
    """Delete food item"""
    try:
        food = food_service.get_food_by_id(food_id)
        if not food:
            return {
                'data': {
                    'code': 'FOOD_NOT_FOUND',
                    'message': 'Food item not found',
                    'details': None
                }
            }, 404
        
        # Check if user owns the camp
        user = get_current_user()
        # Add authorization check if needed
        
        success = food_service.delete_food(food_id)
        if not success:
            return {
                'data': {
                    'code': 'DELETE_FAILED',
                    'message': 'Failed to delete food item',
                    'details': None
                }
            }, 400
        
        return {
            'data': {
                'message': 'Food item deleted successfully'
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
        current_app.logger.error(f"Delete food error: {str(e)}")
        return {
            'data': {
                'code': 'DELETE_FOOD_ERROR',
                'message': 'Failed to delete food item',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.get('/<camp_id>/foods/stats')
@camp_bp.output({
    'type': 'object',
    'properties': {
        'data': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'string'},
                    'name': {'type': 'string'},
                    'quantity': {'type': 'integer'},
                    'vendor': {'type': 'string'},
                    'date': {'type': 'string'},
                    'category': {'type': 'string'},
                    'camp_id': {'type': 'string'},
                    'allocated_quantity': {'type': 'integer'},
                    'available_quantity': {'type': 'integer'},
                    'created_at': {'type': 'string'},
                    'updated_at': {'type': 'string'}
                }
            }
        }
    }
})
@camp_bp.doc(
    summary='Get food allocation statistics',
    description='Get food items with allocation statistics for a camp'
)
@token_required
#@camp_owner_required()
def get_food_stats(camp_id):
    """Get food allocation statistics for camp"""
    try:
        food_stats = food_service.get_food_with_allocation_stats(camp_id)
        
        return {
            'data': food_stats
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Get food stats error: {str(e)}")
        return {
            'data': {
                'code': 'GET_FOOD_STATS_ERROR',
                'message': 'Failed to retrieve food statistics',
                'details': {'error': str(e)}
            }
        }, 500


# =============================================================================
# FOOD ALLOCATION ROUTES
# =============================================================================

@camp_bp.get('/<camp_id>/food-allocations')
@camp_bp.output(FoodAllocationListResponseWrapperSchema)
@camp_bp.doc(
    summary='Get camp food allocations',
    description='Get all food allocations for a camp (Manager only)'
)
@token_required
# #@camp_owner_required()
def get_camp_food_allocations(camp_id):
    """Get all food allocations for camp"""
    try:
        food_category = request.args.get('category')
        allocations = food_allocation_service.get_camp_allocations(camp_id, food_category)
        
        return {
            'data': [allocation.to_dict() for allocation in allocations]
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Get food allocations error: {str(e)}")
        return {
            'data': {
                'code': 'GET_FOOD_ALLOCATIONS_ERROR',
                'message': 'Failed to retrieve food allocations',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.post('/<camp_id>/food-allocations')
@camp_bp.input(FoodAllocationCreateRequestSchema)
# @camp_bp.output(FoodAllocationResponseWrapperSchema, status_code=201)
@camp_bp.doc(
    summary='Allocate food',
    description='Allocate food to a camper registration'
)
@token_required
# #@camp_owner_required()
def allocate_food(camp_id, json_data):
    """Allocate food to camper"""
    try:
        allocation_data = json_data['data']
        allocation_data['camp_id'] = camp_id
        
        user = get_current_user()
        new_allocation = food_allocation_service.allocate_food(allocation_data, str(user.id))
        
        return {
            'data': new_allocation.to_dict()
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
        current_app.logger.error(f"Allocate food error: {str(e)}")
        return {
            'data': {
                'code': 'ALLOCATE_FOOD_ERROR',
                'message': str(e),
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.post('/<camp_id>/food-allocations/bulk')
@camp_bp.input(BulkFoodAllocationRequestSchema)
@camp_bp.output(FoodAllocationListResponseWrapperSchema, status_code=201)
@camp_bp.doc(
    summary='Bulk allocate food',
    description='Allocate food to multiple camper registrations'
)
@token_required
#@camp_owner_required()
def bulk_allocate_food(camp_id, json_data):
    """Bulk allocate food to multiple campers"""
    try:
        allocation_data = json_data['data']
        allocation_data['camp_id'] = camp_id
        
        user = get_current_user()
        
        # Check if allocating by category
        if 'category_id' in allocation_data and allocation_data['category_id']:
            new_allocations = food_allocation_service.allocate_food_by_category(allocation_data, str(user.id))
        else:
            new_allocations = food_allocation_service.bulk_allocate_food(allocation_data, str(user.id))
        
        return {
            'data': [allocation.to_dict() for allocation in new_allocations]
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
        current_app.logger.error(f"Bulk allocate food error: {str(e)}")
        return {
            'data': {
                'code': 'BULK_ALLOCATE_FOOD_ERROR',
                'message': 'Failed to bulk allocate food',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.get('/food-allocations/<allocation_id>')
@camp_bp.output(FoodAllocationResponseWrapperSchema)
@camp_bp.doc(
    summary='Get food allocation details',
    description='Get details of a specific food allocation'
)
@token_required
def get_food_allocation(allocation_id):
    """Get food allocation details"""
    try:
        allocation = food_allocation_service.get_allocation_by_id(allocation_id)
        if not allocation:
            return {
                'data': {
                    'code': 'ALLOCATION_NOT_FOUND',
                    'message': 'Food allocation not found',
                    'details': None
                }
            }, 404
        
        # Check if user owns the camp
        user = get_current_user()
        # Add authorization check if needed
        
        return {
            'data': allocation.to_dict()
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Get food allocation error: {str(e)}")
        return {
            'data': {
                'code': 'GET_FOOD_ALLOCATION_ERROR',
                'message': 'Failed to retrieve food allocation',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.delete('/food-allocations/<allocation_id>')
@camp_bp.output(SuccessMessageWrapperSchema)
@camp_bp.doc(
    summary='Deallocate food',
    description='Remove food allocation for a camper'
)
@token_required
def deallocate_food(allocation_id):
    """Deallocate food from camper"""
    try:
        allocation = food_allocation_service.get_allocation_by_id(allocation_id)
        if not allocation:
            return {
                'data': {
                    'code': 'ALLOCATION_NOT_FOUND',
                    'message': 'Food allocation not found',
                    'details': None
                }
            }, 404
        
        # Check if user owns the camp
        user = get_current_user()
        # Add authorization check if needed
        
        success = food_allocation_service.deallocate_food(allocation_id)
        if not success:
            return {
                'data': {
                    'code': 'DEALLOCATE_FAILED',
                    'message': 'Failed to deallocate food',
                    'details': None
                }
            }, 400
        
        return {
            'data': {
                'message': 'Food allocation removed successfully'
            }
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Deallocate food error: {str(e)}")
        return {
            'data': {
                'code': 'DEALLOCATE_FOOD_ERROR',
                'message': 'Failed to deallocate food',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.get('/<camp_id>/food-allocations/daily-summary')
@camp_bp.output({
    'type': 'object',
    'properties': {
        'data': {
            'type': 'object',
            'properties': {
                'date': {'type': 'string'},
                'categories': {'type': 'object'},
                'total_allocated': {'type': 'integer'},
                'total_available': {'type': 'integer'}
            }
        }
    }
})
@camp_bp.doc(
    summary='Get daily food allocation summary',
    description='Get daily food allocation summary for a camp'
)
@token_required
#@camp_owner_required()
def get_daily_food_summary(camp_id):
    """Get daily food allocation summary for camp"""
    try:
        date_str = request.args.get('date')
        if not date_str:
            from datetime import datetime
            date = datetime.now()
        else:
            from datetime import datetime
            date = datetime.fromisoformat(date_str)
        
        summary = food_allocation_service.get_daily_allocation_summary(camp_id, date)
        
        return {
            'data': summary
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Get daily food summary error: {str(e)}")
        return {
            'data': {
                'code': 'GET_DAILY_SUMMARY_ERROR',
                'message': 'Failed to retrieve daily food summary',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.get('/registrations/<registration_id>/food-allocations')
@camp_bp.output(FoodAllocationListResponseWrapperSchema)
@camp_bp.doc(
    summary='Get camper food allocations',
    description='Get all food allocations for a specific camper'
)
@token_required
def get_camper_food_allocations(registration_id):
    """Get all food allocations for a specific camper"""
    try:
        camp_id = request.args.get('camp_id')
        if not camp_id:
            return {
                'data': {
                    'code': 'MISSING_CAMP_ID',
                    'message': 'Camp ID is required',
                    'details': None
                }
            }, 400
        
        allocations = food_allocation_service.get_registration_allocations(registration_id, camp_id)
        
        return {
            'data': [allocation.to_dict() for allocation in allocations]
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Get camper food allocations error: {str(e)}")
        return {
            'data': {
                'code': 'GET_CAMPER_FOOD_ALLOCATIONS_ERROR',
                'message': 'Failed to retrieve camper food allocations',
                'details': {'error': str(e)}
            }
        }, 500


# =============================================================================
# QR CODE ROUTES
# =============================================================================

@camp_bp.get('/registrations/<registration_id>/qr-code')
@camp_bp.output({
    'type': 'object',
    'properties': {
        'data': {
            'type': 'object',
            'properties': {
                'qr_code_base64': {'type': 'string'},
                'qr_code_svg': {'type': 'string'},
                'qr_code_html': {'type': 'string'},
                'camper_id': {'type': 'string'},
                'camper_code': {'type': 'string'},
                'camper_name': {'type': 'string'}
            }
        }
    }
})
@camp_bp.doc(
    summary='Generate QR code for camper',
    description='Generate QR code for a fully paid camper registration'
)
def generate_camper_qr_code(registration_id):
    """Generate QR code for a camper registration"""
    try:
        from app.integrations.qr_service import qr_service
        
        # Get registration
        registration = registration_service.get_registration_by_id(registration_id)
        if not registration:
            return {
                'data': {
                    'code': 'REGISTRATION_NOT_FOUND',
                    'message': 'Registration not found',
                    'details': None
                }
            }, 404
        
        # Check if registration is fully paid
        if not registration.is_fully_paid():
            return {
                'data': {
                    'code': 'PAYMENT_INCOMPLETE',
                    'message': 'QR code is only available for fully paid registrations',
                    'details': {
                        'outstanding_balance': float(registration.get_outstanding_balance()),
                        'total_amount': float(registration.total_amount),
                        'total_paid': registration.get_total_payments()
                    }
                }
            }, 400
        
        # Generate QR codes in different formats
        qr_code_base64 = qr_service.generate_camper_qr_code(
            str(registration.id), 
            registration.camper_code, 
            'base64'
        )
        
        qr_code_svg = qr_service.generate_camper_qr_code(
            str(registration.id), 
            registration.camper_code, 
            'svg'
        )
        
        qr_code_html = qr_service.generate_camper_qr_code(
            str(registration.id), 
            registration.camper_code, 
            'html'
        )
        
        camper_name = f"{registration.surname} {registration.last_name}"
        
        return {
            'data': {
                'qr_code_base64': qr_code_base64,
                'qr_code_svg': qr_code_svg,
                'qr_code_html': qr_code_html,
                'camper_id': str(registration.id),
                'camper_code': registration.camper_code,
                'camper_name': camper_name
            }
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Generate QR code error: {str(e)}")
        return {
            'data': {
                'code': 'QR_CODE_GENERATION_ERROR',
                'message': 'Failed to generate QR code',
                'details': {'error': str(e)}
            }
        }, 500


@camp_bp.post('/qr-code/decode')
@camp_bp.input({
    'type': 'object',
    'properties': {
        'data': {
            'type': 'object',
            'properties': {
                'qr_data': {'type': 'string', 'description': 'The QR code data string to decode'}
            },
            'required': ['qr_data']
        }
    },
    'required': ['data']
})
@camp_bp.output({
    'type': 'object',
    'properties': {
        'data': {
            'type': 'object',
            'properties': {
                'camper_id': {'type': 'string'},
                'camper_code': {'type': 'string'},
                'type': {'type': 'string'},
                'registration': {'type': 'object'}
            }
        }
    }
})
@camp_bp.doc(
    summary='Decode QR code data',
    description='Decode QR code data and return camper information'
)
@token_required
def decode_qr_code(json_data):
    """Decode QR code data and return camper information"""
    try:
        from app.integrations.qr_service import qr_service
        
        qr_data = json_data['data']['qr_data']
        
        # Decode QR code data
        decoded_data = qr_service.decode_camper_qr_data(qr_data)
        
        # Get registration information
        registration = registration_service.get_registration_by_id(decoded_data['camper_id'])
        if not registration:
            return {
                'data': {
                    'code': 'REGISTRATION_NOT_FOUND',
                    'message': 'Registration not found for this QR code',
                    'details': None
                }
            }, 404
        
        # Return decoded data with registration info
        registration_data = registration.to_dict(include_payments=True)
        registration_data["church"] = registration.church.to_dict(
            for_api=False, include_registrations=False
        )
        
        return {
            'data': {
                'camper_id': decoded_data['camper_id'],
                'camper_code': decoded_data['camper_code'],
                'type': decoded_data['type'],
                'registration': registration_data
            }
        }, 200
        
    except ValueError as e:
        return {
            'data': {
                'code': 'INVALID_QR_CODE',
                'message': str(e),
                'details': None
            }
        }, 400
    except Exception as e:
        current_app.logger.error(f"Decode QR code error: {str(e)}")
        return {
            'data': {
                'code': 'QR_CODE_DECODE_ERROR',
                'message': 'Failed to decode QR code',
                'details': {'error': str(e)}
            }
        }, 500


# =============================================================================
# QR EMAIL ROUTE
# =============================================================================

@camp_bp.post('/send-email')
@camp_bp.input(EmailQrSchema)
@camp_bp.output(SuccessMessageWrapperSchema)
@camp_bp.doc(
    summary='Send camper QR code email',
    description='Queues an email to the camper with their QR code using the existing HTML template. Requires registration to be fully paid.'
)
@token_required
def email_qr_code(json_data):
    """Send QR code email to a camper (queues async send)"""
    try:
        # Get registration
        registration = registration_service.get_registration_by_camper_code(json_data['camperCode'])
        if not registration:
            return {
                'data': {
                    'code': 'REGISTRATION_NOT_FOUND',
                    'message': 'Registration not found',
                    'details': None
                }
            }, 404

        # Ensure camper is fully paid before sending QR
        # if not registration.is_fully_paid():
        #     return {
        #         'data': {
        #             'code': 'PAYMENT_INCOMPLETE',
        #             'message': 'QR code email is only available for fully paid registrations',
        #             'details': {
        #                 'outstanding_balance': float(registration.get_outstanding_balance()),
        #                 'total_amount': float(registration.total_amount),
        #                 'total_paid': registration.get_total_payments()
        #             }
        #         }
        #     }, 400

        # Determine recipient
        req_data = json_data
        to = req_data.get('to')
        recipients = [to] if to else ([registration.email] if registration.email else [])
        if not recipients:
            return {
                'data': {
                    'code': 'MISSING_EMAIL',
                    'message': 'No recipient email provided and registration has no email',
                    'details': None
                }
            }, 400

        # Build email content
        from app.integrations.mailer import mailer
        from app.integrations.qr_service import qr_service
        from app.integrations.threading_utils import threaded_service, send_email_threaded

        camp_name = registration.camp.name
        camper_name = f"{registration.surname} {registration.last_name}"

        # Generate QR in HTML (for embedding) and Base64 (for optional attachment)

        template_context = {
            'camp_name': camp_name,
            'camper_name': camper_name,
            'camper_code': registration.camper_code,
            'camp_start_date': registration.camp.start_date.strftime('%B %d, %Y'),
            'qr_code_cid': f"qr_{registration.camper_code}.png",
            'support_email': 'support@wedidtech.com'
        }

        html_content = mailer.generate_email_text('qr-code.html', template_context)
        subject = req_data.get('subject') or f"Your QR Code - {camp_name}"

        # Optional PNG attachment
        attachments = None
        if req_data.get('qrBase64', False):
            attachments = [{
                'filename': f"qr_{registration.camper_code}.png",
                'fileblob': json_data['qrBase64'],
                'mimetype': 'image/png'
            }]

        # Queue email send on background thread
        threaded_service.execute_in_thread(
            send_email_threaded,
            mailer,
            recipients,
            subject,
            html_content,
            None,
            True,
            attachments
        )

        return {
            'data': {
                'message': 'QR code email queued for delivery'
            }
        }, 200

    except Exception as e:
        current_app.logger.error(f"Email QR code error: {str(e)}")
        return {
            'data': {
                'code': 'EMAIL_QR_ERROR',
                'message': 'Failed to send QR code email',
                'details': {'error': str(e)}
            }
        }, 500


# =============================================================================


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
