"""
Flask extensions initialization

This module initializes all Flask extensions used in the application.
Extensions are created here and initialized in the application factory.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_bcrypt import Bcrypt
import traceback

# Database
db = SQLAlchemy()

# Database migrations
migrate = Migrate()

# JWT authentication
jwt = JWTManager()

# CORS (Cross-Origin Resource Sharing)
cors = CORS()

# Bcrypt
bcrypt = Bcrypt()

# Rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000 per hour", "100 per minute"]
)


def init_extensions(app):
    """Initialize Flask extensions with the app instance"""
    
    # Initialize database
    db.init_app(app)
    
    # Initialize migrations
    migrate.init_app(app, db)
    
    # Initialize JWT
    jwt.init_app(app)
    
    # Initialize CORS
    cors.init_app(app, 
                  origins=app.config.get('CORS_ORIGINS', ['*']),
                  methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
                  allow_headers=['Content-Type', 'Authorization'],
                  supports_credentials=True)
    
    # Initialize rate limiter
    # limiter.init_app(app)
    
    # Configure JWT callbacks
    configure_jwt_callbacks(app)


def configure_jwt_callbacks(app):
    """Configure JWT callback functions"""
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        """Handle expired tokens"""
        return {
            'data': {
                'code': 'TOKEN_EXPIRED',
                'message': 'Token has expired',
                'details': None
            }
        }, 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        """Handle invalid tokens"""
        return {
            'data': {
                'code': 'INVALID_TOKEN',
                'message': 'Invalid token',
                'details': {'error': str(error)}
            }
        }, 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        """Handle missing tokens"""
        return {
            'data': {
                'code': 'MISSING_TOKEN',
                'message': 'Authentication token required',
                'details': None
            }
        }, 401
    
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        """Handle revoked tokens"""
        return {
            'data': {
                'code': 'TOKEN_REVOKED',
                'message': 'Token has been revoked',
                'details': None
            }
        }, 401
    
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        """Check if token is in blocklist (implement with Redis in production)"""
        # TODO: Implement token blacklisting with Redis
        # For now, no tokens are blocked
        return False
    
    # @jwt.additional_claims_loader
    # def add_claims_to_jwt(identity):
    #     """Add additional claims to JWT tokens"""
    #     # Import here to avoid circular imports
    #     from .user.models import User
        
    #     # Identity is already a string, so we can use it directly
    #     user = User.query.filter_by(id=identity).first()
    #     if user:
    #         return {
    #             'email': user.email,
    #             'role': user.role,
    #             'full_name': user.full_name
    #         }
    #     return {}
    
    @jwt.user_identity_loader
    def user_identity_lookup(user):
        """Define how to get user identity for JWT"""
        if hasattr(user, 'id'):
            return str(user.id)
        return str(user)
    
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        """Load user object from JWT"""
        # Import here to avoid circular imports
        from .user.models import User
        
        identity = jwt_data["sub"]
        return User.query.filter_by(id=identity).first()


def register_error_handlers(app):
    """Register global error handlers"""
    
    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request"""
        return {
            'data': {
                'code': 'BAD_REQUEST',
                'message': 'Bad request',
                'details': {'error': str(error)}
            }
        }, 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        """Handle 401 Unauthorized"""
        return {
            'data': {
                'code': 'UNAUTHORIZED',
                'message': 'Authentication required',
                'details': None
            }
        }, 401
    
    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 Forbidden"""
        return {
            'data': {
                'code': 'FORBIDDEN',
                'message': 'Access denied',
                'details': None
            }
        }, 403
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found"""
        return {
            'data': {
                'code': 'NOT_FOUND',
                'message': 'Resource not found',
                'details': None
            }
        }, 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        """Handle 405 Method Not Allowed"""
        return {
            'data': {
                'code': 'METHOD_NOT_ALLOWED',
                'message': 'Method not allowed',
                'details': None
            }
        }, 405
    
    @app.errorhandler(409)
    def conflict(error):
        """Handle 409 Conflict"""
        return {
            'data': {
                'code': 'CONFLICT',
                'message': 'Resource conflict',
                'details': {'error': str(error)}
            }
        }, 409
    
    @app.errorhandler(422)
    def unprocessable_entity(error):
        """Handle 422 Unprocessable Entity (validation errors)"""
        return {
            'data': {
                'code': 'VALIDATION_ERROR',
                'message': 'Validation failed',
                'details': error.description if hasattr(error, 'description') else {'error': str(error)}
            }
        }, 422
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        """Handle 429 Too Many Requests"""
        return {
            'data': {
                'code': 'RATE_LIMIT_EXCEEDED',
                'message': 'Rate limit exceeded',
                'details': {'retry_after': error.retry_after if hasattr(error, 'retry_after') else None}
            }
        }, 429
    
    @app.errorhandler(500)
    def internal_server_error(error):
        """Handle 500 Internal Server Error"""
        app.logger.error(f"Internal server error: {str(error)}")
        app.logger.error(traceback.format_exc())
        return {
            'data': {
                'code': 'INTERNAL_ERROR',
                'message': 'Internal server error',
                'details': None
            }
        }, 500
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Handle unexpected errors"""
        app.logger.error(f"Unexpected error: {str(error)}", exc_info=True)
        app.logger.error(traceback.format_exc())
        return {
            'data': {
                'code': 'UNEXPECTED_ERROR',
                'message': 'An unexpected error occurred',
                'details': str(error)
            }
        }, 500


def register_cli_commands(app):
    """Register CLI commands for the application"""
    
    @app.cli.command()
    def init_db():
        """Initialize the database"""
        from .user.models import User
        from .camp.models import Camp, Church, Category, CustomField, RegistrationLink, Registration
        
        db.create_all()
        print("Database initialized successfully!")
    
    @app.cli.command()
    def drop_db():
        """Drop all database tables"""
        db.drop_all()
        print("Database dropped successfully!")
    
    @app.cli.command()
    def reset_db():
        """Reset the database (drop and recreate)"""
        db.drop_all()
        db.create_all()
        print("Database reset successfully!")
    
    @app.cli.command()
    def create_admin():
        """Create an admin user"""
        from .user.models import User
        from flask_bcrypt import generate_password_hash
        
        email = input("Admin email: ")
        password = input("Admin password: ")
        full_name = input("Admin full name: ")
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            print("User with this email already exists!")
            return
        
        admin_user = User(
            email=email,
            full_name=full_name,
            role='camp_manager'
        )
        admin_user.set_password(password)
        
        db.session.add(admin_user)
        db.session.commit()
        
        print(f"Admin user created successfully: {email}")
    
    @app.cli.command()
    def test_db():
        """Test database connection"""
        try:
            db.session.execute('SELECT 1')
            print("Database connection successful!")
        except Exception as e:
            print(f"Database connection failed: {str(e)}")


def register_shell_context(app):
    """Register shell context for flask shell command"""
    
    @app.shell_context_processor
    def make_shell_context():
        """Make database models available in flask shell"""
        from .user.models import User
        from .camp.models import Camp, Church, Category, CustomField, RegistrationLink, Registration
        
        return {
            'db': db,
            'User': User,
            'Camp': Camp,
            'Church': Church,
            'Category': Category,
            'CustomField': CustomField,
            'RegistrationLink': RegistrationLink,
            'Registration': Registration
        }
