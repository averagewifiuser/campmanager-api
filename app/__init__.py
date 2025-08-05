"""
CampManager API Application Factory

This module contains the application factory function that creates and configures
the Flask application instance with all necessary extensions and blueprints.
"""

import os
from apiflask import APIFlask
from flask import request
from datetime import datetime, timezone
from dotenv import load_dotenv
import logging
from logging import getLogger, basicConfig
from logging.config import dictConfig
import sys

# Load environment variables from .env file
load_dotenv()

from config import get_config
from .extensions import (
    init_extensions, 
    register_error_handlers, 
    register_cli_commands, 
    register_shell_context
)
from ._shared.auth import AuthMiddleware

from flask_migrate import upgrade


def create_production_app():
    """Create production app instance"""
    return create_app('production')


# Export commonly used functions and classes
__all__ = [
    'create_app',
    'create_development_app', 
    'create_testing_app',
    'create_production_app'
]

def create_app(config_name=None):
    """
    Application factory function

    Args:
        config_name: Configuration name ('development', 'testing', 'production')

    Returns:
        Configured Flask application instance
    """

    # Determine configuration
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    config_class = get_config(config_name)

    # Configure root logger BEFORE app instantiation
    # setting the logging level
    
    dictConfig({
        'version': 1,
        'formatters': {'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        }},
        'handlers': {'wsgi': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://flask.logging.wsgi_errors_stream',
            'formatter': 'default'
        }},
        'root': {
            'level': 'INFO',
            'handlers': ['wsgi']
        }
    })
    
    # Create APIFlask app
    app = APIFlask(
        __name__,
        instance_relative_config=True,
        title=config_class.INFO['title'],
        version=config_class.INFO['version']
    )

    # Load and apply configuration
    app.config.from_object(config_class)
    config_class.init_app(app)

    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize extensions
    init_extensions(app)

    # Auth middleware
    auth_middleware = AuthMiddleware(app)

    # Register components
    register_error_handlers(app)
    register_cli_commands(app)
    register_shell_context(app)
    register_blueprints(app)
    # register_request_hooks(app)
    configure_api_docs(app)

    # Run DB migrations at startup
    with app.app_context():
        upgrade()

    return app


def register_blueprints(app: APIFlask):
    """Register application blueprints"""
    
    # User authentication routes
    from .user.routes import user_bp
    app.register_blueprint(user_bp)
    
    # Camp management routes
    from .camp.routes import camp_bp
    app.register_blueprint(camp_bp)
    
    # Public registration routes
    from .camp.public_routes import public_bp
    app.register_blueprint(public_bp)
    
    # Health check route
    @app.route('/health')
    def health_check():
        """Basic health check endpoint"""
        return {
            'data': {
                'status': 'healthy',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'version': app.config.get('VERSION', '1.0.0')
            }
        }, 200
    
    # API info route
    @app.route('/')
    def api_info():
        """API information endpoint"""
        return {
            'data': {
                'name': 'CampManager API',
                'version': app.config.get('VERSION', '1.0.0'),
                'description': 'A comprehensive camp management system API for church camps',
                'documentation': '/docs',
                'openapi_spec': '/openapi.json',
                'endpoints': {
                    'authentication': '/auth',
                    'camps': '/camps',
                    'public_registration': '/register',
                    'health': '/health'
                }
            }
        }, 200
  

    @app.teardown_appcontext
    def close_db(exception):
        if exception:
            logger.error(f"Request teardown with exception: {str(exception)}")

def configure_api_docs(app: APIFlask):
    """Configure APIFlask documentation"""
    
    # Set API documentation info
    app.config['INFO'] = {
        'title': 'CampManager API',
        'version': '1.0.0',
        'description': '''
# CampManager API

A comprehensive camp management system designed for church camps. 

## Features

- **User Management**: Authentication and authorization for camp managers and volunteers
- **Camp Management**: Create and manage multiple camps with detailed configurations
- **Registration System**: Public and category-specific registration with custom fields
- **Church Management**: Organize participants by church affiliations
- **Category System**: Different registration categories with discount structures
- **Registration Links**: Share category-specific registration links with usage limits
- **Real-time Statistics**: Track registrations, payments, and camp capacity

## Authentication

This API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## Response Format

All API responses follow a consistent format:

```json
{
  "data": {
    // Response data here
  }
}
```

## Error Handling

Errors are returned in the same format with appropriate HTTP status codes:

```json
{
  "data": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {
      // Additional error details (optional)
    }
  }
}
```

## Rate Limiting

API requests are rate limited to prevent abuse. Default limits:
- 1000 requests per hour
- 100 requests per minute

Rate limit headers are included in responses.
        ''',
        'contact': {
            'name': 'CampManager Support',
            'email': 'support@campmanager.com'
        },
        'license': {
            'name': 'MIT',
            'url': 'https://opensource.org/licenses/MIT'
        }
    }
    
    # Set API tags for better organization
    app.config['TAGS'] = [
        {
            'name': 'Authentication',
            'description': 'User registration, login, and profile management'
        },
        {
            'name': 'Camps',
            'description': 'Camp creation, management, and statistics'
        },
        {
            'name': 'Churches',
            'description': 'Church management within camps'
        },
        {
            'name': 'Categories',
            'description': 'Registration category management with discount structures'
        },
        {
            'name': 'Custom Fields',
            'description': 'Dynamic form fields for registration customization'
        },
        {
            'name': 'Registration Links',
            'description': 'Category-specific registration links with access control'
        },
        {
            'name': 'Registrations',
            'description': 'Registration management, payment tracking, and check-in'
        },
        {
            'name': 'Public',
            'description': 'Public registration endpoints accessible via registration links'
        }
    ]
    
    # Set servers for different environments
    app.config['SERVERS'] = [
        {
            'url': 'http://localhost:5000',
            'description': 'Development server'
        },
        {
            'url': 'https://api.campmanager.com',
            'description': 'Production server'
        }
    ]
    
    # Security schemes for authentication
    app.config['SECURITY_SCHEMES'] = {
        'BearerAuth': {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
            'description': 'JWT token obtained from the /auth/login endpoint'
        }
    }
    
    # Configure spec plugins
    app.config['SPEC_PLUGINS'] = [
        'apispec.ext.marshmallow'
    ]
    
    # Local API documentation path
    app.config['LOCAL_SPEC_PATH'] = 'openapi.json'
    
    # Swagger UI configuration
    app.config['SWAGGER_UI_BUNDLE_JS'] = 'https://cdn.jsdelivr.net/npm/swagger-ui-dist@4.15.5/swagger-ui-bundle.js'
    app.config['SWAGGER_UI_STANDALONE_PRESET_JS'] = 'https://cdn.jsdelivr.net/npm/swagger-ui-dist@4.15.5/swagger-ui-standalone-preset.js'
    app.config['SWAGGER_UI_CSS'] = 'https://cdn.jsdelivr.net/npm/swagger-ui-dist@4.15.5/swagger-ui.css'
    
    # Redoc configuration
    app.config['REDOC_STANDALONE_JS'] = 'https://cdn.jsdelivr.net/npm/redoc@2.0.0/bundles/redoc.standalone.js'


# Create application instance for imports
def create_development_app():
    """Create development app instance"""
    return create_app('development')


def create_testing_app():
    """Create testing app instance"""
    return create_app('testing')


def create_production_app():
    """Create production app instance"""
    return create_app('production')
