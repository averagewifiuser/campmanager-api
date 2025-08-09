from flask import request, current_app
from apiflask import APIBlueprint

from .models import RegistrationLink
from app._shared.schemas import ErrorResponseWrapperSchema
from .schemas import (
    RegistrationCreateRequestSchema,
    RegistrationResponseWrapperSchema,
    RegistrationFormResponseWrapperSchema
)
from .services import RegistrationService, CampService
from .._shared.auth import optional_auth
from ..integrations.mailer import Mailer


# Create APIBlueprint for public registration endpoints
public_bp = APIBlueprint('public', __name__, url_prefix='/register')

# Initialize service
registration_service = RegistrationService()
camp_service = CampService()


@public_bp.get('/<link_token>')
@public_bp.output(RegistrationFormResponseWrapperSchema)
@public_bp.doc(
    summary='Get category-specific registration form',
    description='Get registration form structure for category-specific access via registration link'
)
@optional_auth
def get_registration_form_by_token(link_token):
    """Get category-specific registration form structure"""
    try:
        # Get registration link and validate
        link = RegistrationLink.query.filter_by(link_token=link_token).first()
        if not link:
            return {
                'data': {
                    'code': 'INVALID_LINK',
                    'message': 'Invalid registration link',
                    'details': None
                }
            }, 404
        
        # Check if link is valid (active, not expired, under usage limit)
        if not link.is_valid():
            return {
                'data': {
                    'code': 'LINK_EXPIRED',
                    'message': 'Registration link has expired or reached usage limit',
                    'details': None
                }
            }, 410  # Gone
        
        print(link)
        # Get form data using the link token
        form_data = registration_service.get_registration_form(str(link.camp_id), link_token)
        if not form_data:
            return {
                'data': {
                    'code': 'REGISTRATION_UNAVAILABLE',
                    'message': 'Registration is not available for this camp',
                    'details': None
                }
            }, 404
        
        return {
            'data': form_data
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Get registration form by token error: {str(e)}")
        return {
            'data': {
                'code': 'GET_FORM_ERROR',
                'message': 'Failed to retrieve registration form',
                'details': {'error': str(e)}
            }
        }, 500


@public_bp.post('/<link_token>')
@public_bp.input(RegistrationCreateRequestSchema)
@public_bp.output(RegistrationResponseWrapperSchema, status_code=201)
@public_bp.doc(
    summary='Submit category-specific registration',
    description='Submit registration via category-specific registration link'
)
def submit_registration_by_token(link_token, json_data):
    """Submit registration through category-specific link"""
    try:
        # Get registration link and validate
        link = RegistrationLink.query.filter_by(link_token=link_token).first()
        if not link:
            return {
                'data': {
                    'code': 'INVALID_LINK',
                    'message': 'Invalid registration link',
                    'details': None
                }
            }, 404
        
        # Check if link is valid (active, not expired, under usage limit)
        if not link.is_valid():
            return {
                'data': {
                    'code': 'LINK_EXPIRED',
                    'message': 'Registration link has expired or reached usage limit',
                    'details': None
                }
            }, 410  # Gone
        
        registration_data = json_data['data']
        registration_data['camp_id'] = str(link.camp_id)
        
        # Validate that selected category is allowed for this link
        selected_category_id = registration_data.get('category_id')
        if not selected_category_id or selected_category_id not in link.allowed_categories:
            return {
                'data': {
                    'code': 'INVALID_CATEGORY',
                    'message': 'Selected category is not allowed for this registration link',
                    'details': {
                        'allowed_categories': link.allowed_categories,
                        'selected_category': selected_category_id
                    }
                }
            }, 400
        
        # Create registration
        new_registration = registration_service.create_registration(registration_data, link_token)
        camp = camp_service.get_camp_by_id(str(link.camp_id))

        mailer = Mailer()
        message = mailer.generate_email_text('registration-successful.html', {
            "camp_name": camp.name,
            "participant_surname": new_registration.surname,
            "participant_middle_name": new_registration.middle_name,
            "participant_last_name": new_registration.last_name,
            "camper_code": new_registration.camper_code,
            "total_amount": new_registration.total_amount,
            "is_paid": new_registration.has_paid,
            "payment_status": "Paid" if new_registration.has_paid else "Payment Pending",
            "registration_date": new_registration.created_at,
            "camp_start_date": camp.start_date,
            "camp_end_date": camp.end_date,
            "camp_location": camp.location,
            "camp_registration_deadline": camp.registration_deadline,
            "support_email": "support@campmanager.com"
        })
        message = f"Your registration for {camp.name} is successful! Your camp code is {new_registration.camper_code}."
        mailer.send_email(
            recipients=[new_registration.email],
            subject='Registration Successful',
            text=message,
            html=False,
        )
        
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
        current_app.logger.error(f"Submit registration by token error: {str(e)}")
        return {
            'data': {
                'code': 'REGISTRATION_ERROR',
                'message': 'Failed to submit registration',
                'details': {'error': str(e)}
            }
        }, 500


@public_bp.get('/check/<link_token>')
@public_bp.output({
    '200': {
        'description': 'Link status check',
        'schema': {
            'type': 'object',
            'properties': {
                'data': {
                    'type': 'object',
                    'properties': {
                        'is_valid': {'type': 'boolean'},
                        'camp_name': {'type': 'string'},
                        'link_name': {'type': 'string'},
                        'expires_at': {'type': 'string', 'format': 'date-time'},
                        'usage_count': {'type': 'integer'},
                        'usage_limit': {'type': 'integer'},
                        'registration_deadline': {'type': 'string', 'format': 'date-time'},
                        'camp_capacity': {'type': 'integer'},
                        'current_registrations': {'type': 'integer'}
                    }
                }
            }
        }
    },
    '404': ErrorResponseWrapperSchema
})
@public_bp.doc(
    summary='Check registration link status',
    description='Check if registration link is valid and get basic information'
)
def check_registration_link(link_token):
    """Check registration link status and availability"""
    try:
        # Get registration link
        link = RegistrationLink.query.filter_by(link_token=link_token).first()
        if not link:
            return {
                'data': {
                    'code': 'INVALID_LINK',
                    'message': 'Invalid registration link',
                    'details': None
                }
            }, 404
        
        # Get camp info
        camp = link.camp
        current_registrations = len(camp.registrations)
        
        # Check various validity conditions
        is_valid = link.is_valid()
        
        # Additional checks for overall registration availability
        if camp.registration_deadline and camp.registration_deadline.replace(tzinfo=None) < request.current_time:
            is_valid = False
        
        if current_registrations >= camp.capacity:
            is_valid = False
        
        # Safely handle datetime serialization - commented out to avoid isoformat errors
        expires_at_str = str(link.expires_at) if link.expires_at else None
        registration_deadline_str = str(camp.registration_deadline) if camp.registration_deadline else None
        
        # expires_at_str = None
        # if link.expires_at:
        #     if hasattr(link.expires_at, 'isoformat'):
        #         expires_at_str = link.expires_at.isoformat()
        #     else:
        #         expires_at_str = str(link.expires_at)
        
        # registration_deadline_str = None
        # if camp.registration_deadline:
        #     if hasattr(camp.registration_deadline, 'isoformat'):
        #         registration_deadline_str = camp.registration_deadline.isoformat()
        #     else:
        #         registration_deadline_str = str(camp.registration_deadline)
        
        return {
            'data': {
                'is_valid': is_valid,
                'camp_name': camp.name,
                'link_name': link.name,
                'expires_at': expires_at_str,
                'usage_count': link.usage_count,
                'usage_limit': link.usage_limit,
                'registration_deadline': registration_deadline_str,
                'camp_capacity': camp.capacity,
                'current_registrations': current_registrations
            }
        }, 200
        
    except Exception as e:
        current_app.logger.error(f"Check registration link error: {str(e)}")
        return {
            'data': {
                'code': 'CHECK_LINK_ERROR',
                'message': 'Failed to check registration link',
                'details': {'error': str(e)}
            }
        }, 500


# Error handlers for the public blueprint
@public_bp.errorhandler(400)
def bad_request(error):
    """Handle bad request errors"""
    return {
        'data': {
            'code': 'BAD_REQUEST',
            'message': 'Bad request',
            'details': {'error': str(error)}
        }
    }, 400


@public_bp.errorhandler(422)
def validation_error(error):
    """Handle validation errors"""
    return {
        'data': {
            'code': 'VALIDATION_ERROR',
            'message': 'Validation failed',
            'details': error.description if hasattr(error, 'description') else {'error': str(error)}
        }
    }, 422


@public_bp.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    current_app.logger.error(f"Internal error in public routes: {str(error)}")
    return {
        'data': {
            'code': 'INTERNAL_ERROR',
            'message': 'Internal server error',
            'details': None
        }
    }, 500
