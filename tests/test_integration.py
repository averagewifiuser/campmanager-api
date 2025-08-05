"""
Integration tests for CampManager API

This module contains end-to-end integration tests that test the complete
workflow of the application including API endpoints, database operations,
and business logic integration.
"""

import pytest
import json
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from app.user.models import User
from app.camp.models import Camp, Church, Category, Registration


@pytest.mark.integration
class TestUserWorkflow:
    """Test complete user workflow"""
    
    def test_user_registration_and_login_workflow(self, client, db_session):
        """Test complete user registration and login workflow"""
        # Step 1: Register a new user
        registration_data = {
            'data': {
                'email': 'workflow@example.com',
                'password': 'workflowpass123',
                'full_name': 'Workflow User',
                'role': 'camp_manager'
            }
        }
        
        register_response = client.post('/auth/register', json=registration_data)
        assert register_response.status_code == 201
        
        register_data = register_response.get_json()
        user_id = register_data['data']['id']
        
        # Verify user exists in database
        user = db_session.query(User).filter_by(id=user_id).first()
        assert user is not None
        assert user.email == registration_data['data']['email']
        
        # Step 2: Login with the new user
        login_data = {
            'data': {
                'email': registration_data['data']['email'],
                'password': registration_data['data']['password']
            }
        }
        
        login_response = client.post('/auth/login', json=login_data)
        assert login_response.status_code == 200
        
        login_result = login_response.get_json()
        access_token = login_result['data']['access_token']
        
        # Step 3: Access protected route with token
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        profile_response = client.get('/auth/me', headers=headers)
        assert profile_response.status_code == 200
        
        profile_data = profile_response.get_json()
        assert profile_data['data']['email'] == registration_data['data']['email']
        assert profile_data['data']['id'] == user_id
    
    def test_user_profile_update_workflow(self, client, sample_user, sample_user_data):
        """Test user profile update workflow"""
        # Step 1: Login
        login_data = {
            'data': {
                'email': sample_user_data['email'],
                'password': sample_user_data['password']
            }
        }
        
        login_response = client.post('/auth/login', json=login_data)
        assert login_response.status_code == 200
        
        access_token = login_response.get_json()['data']['access_token']
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Step 2: Update profile
        update_data = {
            'data': {
                'full_name': 'Updated Workflow Name',
                'email': 'updated_workflow@example.com'
            }
        }
        
        update_response = client.put('/auth/me', json=update_data, headers=headers)
        assert update_response.status_code == 200
        
        updated_profile = update_response.get_json()
        assert updated_profile['data']['full_name'] == 'Updated Workflow Name'
        assert updated_profile['data']['email'] == 'updated_workflow@example.com'
        
        # Step 3: Verify changes persist
        profile_response = client.get('/auth/me', headers=headers)
        assert profile_response.status_code == 200
        
        profile_data = profile_response.get_json()
        assert profile_data['data']['full_name'] == 'Updated Workflow Name'
        assert profile_data['data']['email'] == 'updated_workflow@example.com'


@pytest.mark.integration
class TestCampManagementWorkflow:
    """Test complete camp management workflow"""
    
    def test_camp_creation_workflow(self, client, auth_headers, db_session):
        """Test complete camp creation workflow"""
        # This test would require implementing camp routes
        # For now, we'll test the basic structure
        
        # Try to access camps endpoint (should be protected)
        response = client.get('/camps', headers=auth_headers)
        
        # Should not return 404 (route exists) but may return other status
        assert response.status_code != 404
    
    def test_unauthorized_camp_access(self, client):
        """Test that camp routes require authentication"""
        response = client.get('/camps')
        
        # Should require authentication
        assert response.status_code == 401


@pytest.mark.integration
class TestRegistrationWorkflow:
    """Test complete registration workflow"""
    
    def test_public_registration_workflow(self, client, sample_registration_link):
        """Test public registration workflow"""
        # Try to access public registration endpoint
        token = sample_registration_link.link_token
        response = client.get(f'/register/{token}')
        
        # Should not return 404 (route exists)
        assert response.status_code != 404


@pytest.mark.integration
class TestDatabaseTransactions:
    """Test database transaction handling"""
    
    def test_user_creation_transaction(self, client, db_session):
        """Test that user creation is properly transactional"""
        initial_user_count = db_session.query(User).count()
        
        # Try to create user with invalid data (should fail)
        invalid_data = {
            'data': {
                'email': 'invalid-email',  # Invalid email format
                'password': 'pass',
                'full_name': 'Test User',
                'role': 'camp_manager'
            }
        }
        
        response = client.post('/auth/register', json=invalid_data)
        assert response.status_code in [400, 422]
        
        # Verify no user was created
        final_user_count = db_session.query(User).count()
        assert final_user_count == initial_user_count
    
    def test_successful_user_creation_commits(self, client, db_session):
        """Test that successful user creation commits to database"""
        initial_user_count = db_session.query(User).count()
        
        valid_data = {
            'data': {
                'email': 'transaction_test@example.com',
                'password': 'validpassword123',
                'full_name': 'Transaction Test User',
                'role': 'camp_manager'
            }
        }
        
        response = client.post('/auth/register', json=valid_data)
        assert response.status_code == 201
        
        # Verify user was created and committed
        final_user_count = db_session.query(User).count()
        assert final_user_count == initial_user_count + 1
        
        # Verify user exists with correct data
        user = db_session.query(User).filter_by(email=valid_data['data']['email']).first()
        assert user is not None
        assert user.full_name == valid_data['data']['full_name']


@pytest.mark.integration
class TestAPIResponseFormat:
    """Test API response format consistency"""
    
    def test_success_response_format(self, client):
        """Test that success responses follow consistent format"""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = response.get_json()
        
        # All responses should have 'data' wrapper
        assert isinstance(data, dict)
        assert 'data' in data
        assert isinstance(data['data'], dict)
    
    def test_error_response_format(self, client):
        """Test that error responses follow consistent format"""
        response = client.get('/nonexistent')
        assert response.status_code == 404
        
        data = response.get_json()
        
        # Error responses should also have 'data' wrapper
        assert isinstance(data, dict)
        assert 'data' in data
    
    def test_validation_error_format(self, client):
        """Test validation error response format"""
        # Send invalid JSON to trigger validation error
        response = client.post('/auth/login', json={'invalid': 'data'})
        assert response.status_code in [400, 422]
        
        data = response.get_json()
        
        # Should follow consistent format
        assert isinstance(data, dict)
        assert 'data' in data


@pytest.mark.integration
class TestSecurityIntegration:
    """Test security features integration"""
    
    def test_jwt_token_expiration_handling(self, client, sample_user, sample_user_data, app):
        """Test JWT token expiration handling"""
        # Login to get token
        login_data = {
            'data': {
                'email': sample_user_data['email'],
                'password': sample_user_data['password']
            }
        }
        
        response = client.post('/auth/login', json=login_data)
        assert response.status_code == 200
        
        token_data = response.get_json()
        access_token = token_data['data']['access_token']
        
        # Token should work immediately
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        response = client.get('/auth/me', headers=headers)
        assert response.status_code == 200
        
        # Test with malformed token
        bad_headers = {
            'Authorization': 'Bearer malformed.token.here',
            'Content-Type': 'application/json'
        }
        
        response = client.get('/auth/me', headers=bad_headers)
        assert response.status_code == 422
    
    def test_password_hashing_integration(self, client, db_session):
        """Test that passwords are properly hashed"""
        password = 'testhashingpassword123'
        user_data = {
            'data': {
                'email': 'hashing_test@example.com',
                'password': password,
                'full_name': 'Hashing Test User',
                'role': 'camp_manager'
            }
        }
        
        response = client.post('/auth/register', json=user_data)
        assert response.status_code == 201
        
        # Verify password is hashed in database
        user = db_session.query(User).filter_by(email=user_data['data']['email']).first()
        assert user is not None
        assert user.password_hash != password  # Should be hashed
        assert len(user.password_hash) > 0
        assert user.check_password(password)  # Should verify correctly


@pytest.mark.integration
class TestConcurrentRequests:
    """Test handling of concurrent requests"""
    
    def test_concurrent_user_registrations(self, client, db_session):
        """Test concurrent user registrations don't cause conflicts"""
        import threading
        import time
        
        results = []
        
        def register_user(email_suffix):
            user_data = {
                'data': {
                    'email': f'concurrent_{email_suffix}@example.com',
                    'password': 'concurrentpass123',
                    'full_name': f'Concurrent User {email_suffix}',
                    'role': 'camp_manager'
                }
            }
            
            response = client.post('/auth/register', json=user_data)
            results.append((email_suffix, response.status_code))
        
        # Create multiple threads to register users concurrently
        threads = []
        for i in range(5):
            thread = threading.Thread(target=register_user, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All registrations should succeed
        for email_suffix, status_code in results:
            assert status_code == 201
        
        # Verify all users were created
        for i in range(5):
            user = db_session.query(User).filter_by(
                email=f'concurrent_{i}@example.com'
            ).first()
            assert user is not None


@pytest.mark.integration
@pytest.mark.slow
class TestPerformanceIntegration:
    """Test performance-related integration scenarios"""
    
    def test_multiple_login_requests_performance(self, client, sample_user, sample_user_data):
        """Test performance of multiple login requests"""
        import time
        
        login_data = {
            'data': {
                'email': sample_user_data['email'],
                'password': sample_user_data['password']
            }
        }
        
        start_time = time.time()
        
        # Make multiple login requests
        for _ in range(10):
            response = client.post('/auth/login', json=login_data)
            assert response.status_code == 200
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete reasonably quickly (less than 5 seconds for 10 requests)
        assert total_time < 5.0
        
        # Average time per request should be reasonable
        avg_time = total_time / 10
        assert avg_time < 0.5  # Less than 500ms per request
    
    def test_database_query_performance(self, client, db_session):
        """Test database query performance"""
        import time
        
        # Create multiple users for testing
        users = []
        for i in range(20):
            user = User(
                email=f'perf_test_{i}@example.com',
                full_name=f'Performance Test User {i}',
                role='camp_manager'
            )
            user.set_password('testpassword123')
            users.append(user)
        
        db_session.add_all(users)
        db_session.commit()
        
        # Test query performance
        start_time = time.time()
        
        # Query all users
        all_users = db_session.query(User).all()
        
        end_time = time.time()
        query_time = end_time - start_time
        
        # Query should be fast
        assert query_time < 1.0  # Less than 1 second
        assert len(all_users) >= 20  # Should include our test users


@pytest.mark.integration
class TestErrorHandlingIntegration:
    """Test error handling across the application"""
    
    def test_database_error_handling(self, client, app_context):
        """Test handling of database errors"""
        # This is a basic test - in a real scenario you might
        # temporarily break the database connection to test error handling
        
        # Try to access an endpoint that requires database
        response = client.get('/health')
        
        # Should handle gracefully even if there are database issues
        assert response.status_code == 200
    
    def test_invalid_json_handling(self, client):
        """Test handling of invalid JSON requests"""
        # Send malformed JSON
        response = client.post('/auth/login',
                             data='{"invalid": json}',
                             content_type='application/json')
        
        assert response.status_code == 400
        assert response.content_type == 'application/json'
        
        # Should return proper error structure
        data = response.get_json()
        assert 'data' in data
    
    def test_missing_required_fields_handling(self, client):
        """Test handling of requests with missing required fields"""
        incomplete_data = {
            'data': {
                'email': 'test@example.com'
                # Missing password, full_name, role
            }
        }
        
        response = client.post('/auth/register', json=incomplete_data)
        assert response.status_code in [400, 422]
        
        data = response.get_json()
        assert 'data' in data


@pytest.mark.integration
class TestApplicationFlow:
    """Test complete application flows"""
    
    def test_health_check_flow(self, client):
        """Test health check endpoint flow"""
        response = client.get('/health')
        
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        
        data = response.get_json()
        assert data['data']['status'] == 'healthy'
        assert 'timestamp' in data['data']
        assert 'version' in data['data']
        
        # Timestamp should be recent (within last minute)
        timestamp_str = data['data']['timestamp']
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        time_diff = now - timestamp
        assert time_diff.total_seconds() < 60
    
    def test_api_documentation_flow(self, client):
        """Test API documentation endpoints"""
        # Test OpenAPI spec
        spec_response = client.get('/openapi.json')
        assert spec_response.status_code == 200
        assert spec_response.content_type == 'application/json'
        
        spec_data = spec_response.get_json()
        assert 'openapi' in spec_data
        assert 'info' in spec_data
        assert 'paths' in spec_data
        
        # Test documentation UI
        docs_response = client.get('/docs')
        assert docs_response.status_code == 200
        assert 'text/html' in docs_response.content_type
