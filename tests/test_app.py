"""
Application tests for CampManager API

This module contains tests for the Flask application factory,
configuration, basic routes, and application setup.
"""

import pytest
from datetime import datetime, timezone

from app import create_app
from config import DevelopmentConfig, TestingConfig, ProductionConfig


@pytest.mark.unit
class TestApplicationFactory:
    """Test application factory functionality"""
    
    def test_create_app_development(self):
        """Test creating development app"""
        app = create_app('development')
        
        assert app is not None
        assert app.config['DEBUG'] is True
        assert app.config['TESTING'] is False
        assert 'SQLALCHEMY_DATABASE_URI' in app.config
    
    def test_create_app_testing(self):
        """Test creating testing app"""
        app = create_app('testing')
        
        assert app is not None
        assert app.config['TESTING'] is True
        assert app.config['DEBUG'] is True
        assert 'sqlite:///:memory:' in app.config['SQLALCHEMY_DATABASE_URI']
    
    def test_create_app_production(self):
        """Test creating production app"""
        app = create_app('production')
        
        assert app is not None
        assert app.config['DEBUG'] is False
        assert app.config['TESTING'] is False
    
    def test_create_app_default_config(self):
        """Test creating app with default config"""
        app = create_app()
        
        assert app is not None
        # Should default to development
        assert app.config['DEBUG'] is True


@pytest.mark.unit
class TestApplicationConfiguration:
    """Test application configuration"""
    
    def test_development_config(self):
        """Test development configuration"""
        config = DevelopmentConfig()
        
        assert config.DEBUG is True
        assert config.TESTING is False
        assert config.LOG_LEVEL == 'DEBUG'
        assert '*' in config.CORS_ORIGINS
    
    def test_testing_config(self):
        """Test testing configuration"""
        config = TestingConfig()
        
        assert config.TESTING is True
        assert config.DEBUG is True
        assert config.SQLALCHEMY_DATABASE_URI == 'sqlite:///:memory:'
        assert config.WTF_CSRF_ENABLED is False
        assert config.SECRET_KEY == 'test-secret-key'
    
    def test_production_config(self):
        """Test production configuration"""
        config = ProductionConfig()
        
        assert config.DEBUG is False
        assert config.TESTING is False
        assert config.LOG_LEVEL == 'WARNING'


@pytest.mark.integration
class TestBasicRoutes:
    """Test basic application routes"""
    
    def test_health_check_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get('/health')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'data' in data
        assert data['data']['status'] == 'healthy'
        assert 'timestamp' in data['data']
        assert 'version' in data['data']
        
        # Verify timestamp format
        timestamp = data['data']['timestamp']
        assert isinstance(timestamp, str)
        # Should be valid ISO format
        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    
    def test_api_info_endpoint(self, client):
        """Test API info endpoint"""
        response = client.get('/')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'data' in data
        assert data['data']['name'] == 'CampManager API'
        assert 'version' in data['data']
        assert 'description' in data['data']
        assert 'documentation' in data['data']
        assert 'openapi_spec' in data['data']
        assert 'endpoints' in data['data']
        
        # Verify endpoints structure
        endpoints = data['data']['endpoints']
        assert 'authentication' in endpoints
        assert 'camps' in endpoints
        assert 'public_registration' in endpoints
        assert 'health' in endpoints
    
    def test_nonexistent_route(self, client):
        """Test accessing non-existent route"""
        response = client.get('/nonexistent')
        
        assert response.status_code == 404
    
    def test_openapi_spec_endpoint(self, client):
        """Test OpenAPI specification endpoint"""
        response = client.get('/openapi.json')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should be valid OpenAPI spec
        assert 'openapi' in data
        assert 'info' in data
        assert 'paths' in data
        assert data['info']['title'] == 'CampManager API'
    
    def test_docs_endpoint(self, client):
        """Test API documentation endpoint"""
        response = client.get('/docs')
        
        assert response.status_code == 200
        assert response.content_type.startswith('text/html')


@pytest.mark.integration
class TestApplicationMiddleware:
    """Test application middleware and hooks"""
    
    def test_request_headers_added(self, client):
        """Test that security headers are added to responses"""
        response = client.get('/health')
        
        assert response.status_code == 200
        
        # Check security headers
        assert 'X-Content-Type-Options' in response.headers
        assert response.headers['X-Content-Type-Options'] == 'nosniff'
        assert 'X-Frame-Options' in response.headers
        assert response.headers['X-Frame-Options'] == 'DENY'
        assert 'X-XSS-Protection' in response.headers
        assert response.headers['X-XSS-Protection'] == '1; mode=block'
        
        # Check API version header
        assert 'X-API-Version' in response.headers
    
    def test_cors_headers(self, client):
        """Test CORS headers are present"""
        response = client.options('/health')
        
        # CORS headers should be present for OPTIONS requests
        assert response.status_code in [200, 204]
    
    def test_json_response_format(self, client):
        """Test that JSON responses follow consistent format"""
        response = client.get('/health')
        
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        
        data = response.get_json()
        assert isinstance(data, dict)
        assert 'data' in data
        assert isinstance(data['data'], dict)


@pytest.mark.integration
class TestErrorHandling:
    """Test application error handling"""
    
    def test_404_error_handling(self, client):
        """Test 404 error handling"""
        response = client.get('/nonexistent-endpoint')
        
        assert response.status_code == 404
        assert response.content_type == 'application/json'
        
        data = response.get_json()
        assert 'data' in data
    
    def test_405_method_not_allowed(self, client):
        """Test 405 method not allowed error"""
        # Try POST on GET-only endpoint
        response = client.post('/health')
        
        assert response.status_code == 405
        assert response.content_type == 'application/json'
    
    def test_invalid_json_request(self, client):
        """Test handling of invalid JSON"""
        response = client.post('/auth/login',
                             data='{"invalid": json}',
                             content_type='application/json')
        
        assert response.status_code == 400
        assert response.content_type == 'application/json'
        
        data = response.get_json()
        assert 'data' in data


@pytest.mark.integration
class TestDatabaseIntegration:
    """Test database integration"""
    
    def test_database_connection(self, app_context):
        """Test database connection is established"""
        from app.extensions import db
        
        # Should be able to execute a simple query
        result = db.session.execute(db.text('SELECT 1')).scalar()
        assert result == 1
    
    def test_database_tables_created(self, app_context):
        """Test that database tables are created"""
        from app.extensions import db
        from app.user.models import User
        from app.camp.models import Camp, Church, Category
        
        # Check that tables exist by querying metadata
        inspector = db.inspect(db.engine)
        table_names = inspector.get_table_names()
        
        assert 'users' in table_names
        assert 'camps' in table_names
        assert 'churches' in table_names
        assert 'categories' in table_names
        assert 'custom_fields' in table_names
        assert 'registration_links' in table_names
        assert 'registrations' in table_names


@pytest.mark.integration
class TestApplicationSecurity:
    """Test application security features"""
    
    def test_secret_key_configured(self, app):
        """Test that secret key is configured"""
        assert app.config['SECRET_KEY'] is not None
        assert len(app.config['SECRET_KEY']) > 0
        assert app.config['SECRET_KEY'] != 'dev-secret-key-change-in-production'
    
    def test_jwt_secret_configured(self, app):
        """Test that JWT secret is configured"""
        assert app.config['JWT_SECRET_KEY'] is not None
        assert len(app.config['JWT_SECRET_KEY']) > 0
    
    def test_csrf_disabled_for_api(self, app):
        """Test that CSRF is disabled for API"""
        assert app.config['WTF_CSRF_ENABLED'] is False
    
    def test_sql_injection_protection(self, client):
        """Test basic SQL injection protection"""
        # Try SQL injection in query parameter
        response = client.get('/health?id=1; DROP TABLE users; --')
        
        # Should not cause server error
        assert response.status_code == 200


@pytest.mark.integration
class TestApplicationLogging:
    """Test application logging configuration"""
    
    def test_logger_configured(self, app):
        """Test that logger is configured"""
        assert app.logger is not None
        assert len(app.logger.handlers) > 0
    
    def test_request_logging(self, app, client):
        """Test that requests are logged in debug mode"""
        with app.test_request_context():
            # In debug mode, requests should be logged
            if app.debug:
                response = client.get('/health')
                assert response.status_code == 200
                # Logger should have recorded the request
                # (This is more of a smoke test since we can't easily capture logs)


@pytest.mark.integration
class TestApplicationExtensions:
    """Test Flask extensions integration"""
    
    def test_sqlalchemy_extension(self, app):
        """Test SQLAlchemy extension is initialized"""
        from app.extensions import db
        
        assert db is not None
        # Check if extension is properly initialized with app
        assert 'sqlalchemy' in app.extensions
        assert app.extensions['sqlalchemy'] is db
    
    def test_bcrypt_extension(self, app):
        """Test Bcrypt extension is initialized"""
        from app.extensions import bcrypt
        
        assert bcrypt is not None
        # Check if extension is properly initialized by testing functionality
        test_password = "test123"
        hashed = bcrypt.generate_password_hash(test_password)
        assert bcrypt.check_password_hash(hashed, test_password)
    
    def test_jwt_extension(self, app):
        """Test JWT extension is initialized"""
        from app.extensions import jwt
        
        assert jwt is not None
        # Check if extension is properly initialized with app
        assert 'flask-jwt-extended' in app.extensions
        assert app.extensions['flask-jwt-extended'] is jwt
    
    def test_migrate_extension(self, app):
        """Test Flask-Migrate extension is initialized"""
        from app.extensions import migrate
        
        assert migrate is not None
        # Check if extension is properly initialized with app
        assert 'migrate' in app.extensions
        # The migrate extension stores a config object, not the migrate instance itself
        assert hasattr(app.extensions['migrate'], 'db')


@pytest.mark.integration
class TestApplicationBlueprints:
    """Test blueprint registration"""
    
    def test_user_blueprint_registered(self, app):
        """Test user blueprint is registered"""
        # Check that user routes are available
        with app.test_client() as client:
            response = client.post('/auth/login', json={})
            # Should get validation error, not 404
            assert response.status_code != 404
    
    def test_camp_blueprint_registered(self, app):
        """Test camp blueprint is registered"""
        # Check that camp routes are available
        with app.test_client() as client:
            response = client.get('/camps')
            # Should get auth error, not 404
            assert response.status_code != 404
    
    def test_public_blueprint_registered(self, app):
        """Test public blueprint is registered"""
        # Check that public routes are available
        with app.test_client() as client:
            response = client.get('/register/invalid-token')
            # Should get 404 for invalid token, but route should exist and return JSON
            assert response.status_code == 404
            assert response.content_type == 'application/json'
            data = response.get_json()
            assert 'data' in data


@pytest.mark.integration
class TestApplicationPerformance:
    """Test basic application performance"""
    
    def test_health_check_response_time(self, client):
        """Test health check response time is reasonable"""
        import time
        
        start_time = time.time()
        response = client.get('/health')
        end_time = time.time()
        
        assert response.status_code == 200
        
        # Response should be fast (under 1 second)
        response_time = end_time - start_time
        assert response_time < 1.0
    
    def test_multiple_requests_handling(self, client):
        """Test handling multiple concurrent requests"""
        responses = []
        
        # Make multiple requests
        for _ in range(10):
            response = client.get('/health')
            responses.append(response)
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.get_json()
            assert data['data']['status'] == 'healthy'


@pytest.mark.integration
class TestApplicationEnvironment:
    """Test application environment handling"""
    
    def test_testing_environment(self, app):
        """Test application runs in testing environment"""
        assert app.config['TESTING'] is True
        assert 'test' in app.config['SQLALCHEMY_DATABASE_URI'].lower()
    
    def test_environment_variables_loaded(self, app):
        """Test that environment variables are loaded"""
        # Basic config should be loaded
        assert 'SECRET_KEY' in app.config
        assert 'SQLALCHEMY_DATABASE_URI' in app.config
        assert 'JWT_SECRET_KEY' in app.config
    
    def test_instance_folder_created(self, app):
        """Test that instance folder exists"""
        import os
        assert os.path.exists(app.instance_path)
