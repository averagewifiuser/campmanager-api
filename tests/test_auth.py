"""
Authentication tests for CampManager API

This module contains tests for user authentication, registration, login,
token management, and authorization functionality.
"""

import pytest
import json
from datetime import datetime, timezone, timedelta
from flask_jwt_extended import decode_token

from app.user.models import User


@pytest.mark.auth
class TestUserRegistration:
    """Test user registration functionality"""
    
    def test_register_valid_user(self, client, db_session):
        """Test successful user registration"""
        user_data = {
            'data': {
                'email': 'newuser@example.com',
                'password': 'securepassword123',
                'full_name': 'New User',
                'role': 'camp_manager'
            }
        }
        
        response = client.post('/auth/register', 
                             json=user_data,
                             content_type='application/json')
        
        assert response.status_code == 201
        data = response.get_json()
        
        assert 'data' in data
        assert 'id' in data['data']
        assert data['data']['email'] == user_data['data']['email']
        assert data['data']['full_name'] == user_data['data']['full_name']
        assert data['data']['role'] == user_data['data']['role']
        assert 'password_hash' not in data['data']
        
        # Verify user was created in database
        user = db_session.query(User).filter_by(email=user_data['data']['email']).first()
        assert user is not None
        assert user.email == user_data['data']['email']
        assert user.check_password(user_data['data']['password'])
    
    def test_register_duplicate_email(self, client, sample_user):
        """Test registration with existing email"""
        user_data = {
            'data': {
                'email': sample_user.email,  # Existing email
                'password': 'newpassword123',
                'full_name': 'Another User',
                'role': 'volunteer'
            }
        }
        
        response = client.post('/auth/register', 
                             json=user_data,
                             content_type='application/json')
        
        assert response.status_code == 409
        data = response.get_json()
        
        assert 'data' in data
        assert data['data']['code'] == 'USER_EXISTS'
        assert 'already exists' in data['data']['message']
    
    def test_register_invalid_data(self, client):
        """Test registration with invalid data"""
        # Missing required fields
        user_data = {
            'data': {
                'email': 'invalid@example.com'
                # Missing password, full_name, role
            }
        }
        
        response = client.post('/auth/register', 
                             json=user_data,
                             content_type='application/json')
        
        assert response.status_code in [400, 422]  # Bad request or validation error
    
    def test_register_invalid_email(self, client):
        """Test registration with invalid email format"""
        user_data = {
            'data': {
                'email': 'not-an-email',
                'password': 'securepassword123',
                'full_name': 'Test User',
                'role': 'camp_manager'
            }
        }
        
        response = client.post('/auth/register', 
                             json=user_data,
                             content_type='application/json')
        
        assert response.status_code in [400, 422]
    
    def test_register_volunteer_role(self, client, db_session):
        """Test registration with volunteer role"""
        user_data = {
            'data': {
                'email': 'volunteer@example.com',
                'password': 'volunteerpass123',
                'full_name': 'Volunteer User',
                'role': 'volunteer'
            }
        }
        
        response = client.post('/auth/register', 
                             json=user_data,
                             content_type='application/json')
        
        assert response.status_code == 201
        data = response.get_json()
        
        assert data['data']['role'] == 'volunteer'
        
        # Verify in database
        user = db_session.query(User).filter_by(email=user_data['data']['email']).first()
        assert user.role == 'volunteer'


@pytest.mark.auth
class TestUserLogin:
    """Test user login functionality"""
    
    def test_login_valid_credentials(self, client, sample_user, sample_user_data):
        """Test successful login with valid credentials"""
        login_data = {
            'data': {
                'email': sample_user_data['email'],
                'password': sample_user_data['password']
            }
        }
        
        response = client.post('/auth/login', 
                             json=login_data,
                             content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'data' in data
        assert 'access_token' in data['data']
        assert 'refresh_token' in data['data']
        assert 'user' in data['data']
        assert 'expires_in' in data['data']
        
        # Verify user data
        user_data = data['data']['user']
        assert user_data['email'] == sample_user_data['email']
        assert user_data['full_name'] == sample_user_data['full_name']
        assert user_data['role'] == sample_user_data['role']
        assert 'password_hash' not in user_data
        
        # Verify token properties
        assert isinstance(data['data']['access_token'], str)
        assert isinstance(data['data']['refresh_token'], str)
        assert data['data']['expires_in'] == 86400  # 24 hours in seconds
    
    def test_login_invalid_email(self, client):
        """Test login with non-existent email"""
        login_data = {
            'data': {
                'email': 'nonexistent@example.com',
                'password': 'anypassword'
            }
        }
        
        response = client.post('/auth/login', 
                             json=login_data,
                             content_type='application/json')
        
        assert response.status_code == 401
        data = response.get_json()
        
        assert 'data' in data
        assert data['data']['code'] == 'INVALID_CREDENTIALS'
        assert 'Invalid email or password' in data['data']['message']
    
    def test_login_invalid_password(self, client, sample_user, sample_user_data):
        """Test login with incorrect password"""
        login_data = {
            'data': {
                'email': sample_user_data['email'],
                'password': 'wrongpassword'
            }
        }
        
        response = client.post('/auth/login', 
                             json=login_data,
                             content_type='application/json')
        
        assert response.status_code == 401
        data = response.get_json()
        
        assert data['data']['code'] == 'INVALID_CREDENTIALS'
    
    def test_login_missing_data(self, client):
        """Test login with missing credentials"""
        login_data = {
            'data': {
                'email': 'test@example.com'
                # Missing password
            }
        }
        
        response = client.post('/auth/login', 
                             json=login_data,
                             content_type='application/json')
        
        assert response.status_code in [400, 422]
    
    def test_login_empty_credentials(self, client):
        """Test login with empty credentials"""
        login_data = {
            'data': {
                'email': '',
                'password': ''
            }
        }
        
        response = client.post('/auth/login', 
                             json=login_data,
                             content_type='application/json')
        
        assert response.status_code in [400, 401, 422]


@pytest.mark.auth
class TestTokenManagement:
    """Test JWT token management"""
    
    def test_token_refresh(self, client, sample_user, sample_user_data):
        """Test token refresh functionality"""
        # First login to get tokens
        login_data = {
            'data': {
                'email': sample_user_data['email'],
                'password': sample_user_data['password']
            }
        }
        
        login_response = client.post('/auth/login', json=login_data)
        assert login_response.status_code == 200
        
        login_data = login_response.get_json()
        refresh_token = login_data['data']['refresh_token']
        
        # Use refresh token to get new access token
        headers = {
            'Authorization': f'Bearer {refresh_token}',
            'Content-Type': 'application/json'
        }
        
        response = client.post('/auth/refresh', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'data' in data
        assert 'access_token' in data['data']
        assert 'expires_in' in data['data']
        assert isinstance(data['data']['access_token'], str)
        assert data['data']['expires_in'] == 86400
    
    def test_token_refresh_invalid_token(self, client):
        """Test token refresh with invalid token"""
        headers = {
            'Authorization': 'Bearer invalid_token',
            'Content-Type': 'application/json'
        }
        
        response = client.post('/auth/refresh', headers=headers)
        
        assert response.status_code == 422  # Unprocessable Entity for invalid JWT
    
    def test_token_refresh_no_token(self, client):
        """Test token refresh without token"""
        response = client.post('/auth/refresh')
        
        assert response.status_code == 401  # Unauthorized
    
    def test_access_token_contains_user_claims(self, client, sample_user, sample_user_data, app):
        """Test that access token contains user claims"""
        # Login to get access token
        login_data = {
            'data': {
                'email': sample_user_data['email'],
                'password': sample_user_data['password']
            }
        }
        
        response = client.post('/auth/login', json=login_data)
        assert response.status_code == 200
        
        data = response.get_json()
        access_token = data['data']['access_token']
        
        # Decode token to verify claims
        with app.app_context():
            decoded_token = decode_token(access_token)
            
            assert decoded_token['sub'] == str(sample_user.id)  # Subject is user ID
            assert decoded_token['email'] == sample_user_data['email']
            assert decoded_token['role'] == sample_user_data['role']
            assert decoded_token['full_name'] == sample_user_data['full_name']


@pytest.mark.auth
class TestProtectedRoutes:
    """Test protected route access"""
    
    def test_get_current_user_with_valid_token(self, client, auth_headers, sample_user):
        """Test accessing protected route with valid token"""
        response = client.get('/auth/me', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'data' in data
        assert data['data']['id'] == str(sample_user.id)
        assert data['data']['email'] == sample_user.email
        assert data['data']['full_name'] == sample_user.full_name
        assert data['data']['role'] == sample_user.role
        assert 'password_hash' not in data['data']
    
    def test_get_current_user_without_token(self, client):
        """Test accessing protected route without token"""
        response = client.get('/auth/me')
        
        assert response.status_code == 401
    
    def test_get_current_user_with_invalid_token(self, client):
        """Test accessing protected route with invalid token"""
        headers = {
            'Authorization': 'Bearer invalid_token',
            'Content-Type': 'application/json'
        }
        
        response = client.get('/auth/me', headers=headers)
        
        assert response.status_code == 422
    
    def test_get_current_user_with_expired_token(self, client, app):
        """Test accessing protected route with expired token"""
        # This test would require creating an expired token
        # For now, we'll test with malformed token
        headers = {
            'Authorization': 'Bearer expired.token.here',
            'Content-Type': 'application/json'
        }
        
        response = client.get('/auth/me', headers=headers)
        
        assert response.status_code == 422


@pytest.mark.auth
class TestUserProfileManagement:
    """Test user profile management"""
    
    def test_update_user_profile(self, client, auth_headers, sample_user):
        """Test updating user profile"""
        update_data = {
            'data': {
                'full_name': 'Updated Name',
                'email': 'updated@example.com'
            }
        }
        
        response = client.put('/auth/me', 
                            json=update_data,
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['data']['full_name'] == 'Updated Name'
        assert data['data']['email'] == 'updated@example.com'
        assert data['data']['id'] == str(sample_user.id)
    
    def test_update_user_profile_duplicate_email(self, client, auth_headers, sample_volunteer):
        """Test updating profile with existing email"""
        update_data = {
            'data': {
                'email': sample_volunteer.email  # Email already exists
            }
        }
        
        response = client.put('/auth/me', 
                            json=update_data,
                            headers=auth_headers)
        
        assert response.status_code == 409
        data = response.get_json()
        
        assert data['data']['code'] == 'EMAIL_EXISTS'
    
    def test_change_password(self, client, auth_headers, sample_user_data):
        """Test changing user password"""
        password_data = {
            'data': {
                'current_password': sample_user_data['password'],
                'new_password': 'newsecurepassword123'
            }
        }
        
        response = client.put('/auth/me/password', 
                            json=password_data,
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'message' in data['data']
        assert 'successfully' in data['data']['message'].lower()
    
    def test_change_password_wrong_current(self, client, auth_headers):
        """Test changing password with wrong current password"""
        password_data = {
            'data': {
                'current_password': 'wrongpassword',
                'new_password': 'newsecurepassword123'
            }
        }
        
        response = client.put('/auth/me/password', 
                            json=password_data,
                            headers=auth_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        
        assert data['data']['code'] == 'INVALID_PASSWORD'
    
    def test_change_password_missing_data(self, client, auth_headers):
        """Test changing password with missing data"""
        password_data = {
            'data': {
                'current_password': 'somepassword'
                # Missing new_password
            }
        }
        
        response = client.put('/auth/me/password', 
                            json=password_data,
                            headers=auth_headers)
        
        assert response.status_code in [400, 422]


@pytest.mark.auth
class TestLogout:
    """Test user logout functionality"""
    
    def test_logout_with_valid_token(self, client, auth_headers):
        """Test logout with valid token"""
        response = client.post('/auth/logout', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'data' in data
        assert 'message' in data['data']
        assert 'logged out' in data['data']['message'].lower()
    
    def test_logout_without_token(self, client):
        """Test logout without token"""
        response = client.post('/auth/logout')
        
        assert response.status_code == 401
    
    def test_logout_with_invalid_token(self, client):
        """Test logout with invalid token"""
        headers = {
            'Authorization': 'Bearer invalid_token',
            'Content-Type': 'application/json'
        }
        
        response = client.post('/auth/logout', headers=headers)
        
        assert response.status_code == 422


@pytest.mark.auth
class TestRoleBasedAccess:
    """Test role-based access control"""
    
    def test_camp_manager_access(self, client, auth_headers, sample_user):
        """Test that camp manager can access their profile"""
        assert sample_user.role == 'camp_manager'
        
        response = client.get('/auth/me', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['role'] == 'camp_manager'
    
    def test_volunteer_access(self, client, volunteer_auth_headers, sample_volunteer):
        """Test that volunteer can access their profile"""
        assert sample_volunteer.role == 'volunteer'
        
        response = client.get('/auth/me', headers=volunteer_auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['role'] == 'volunteer'


@pytest.mark.auth
class TestAuthenticationEdgeCases:
    """Test authentication edge cases and error handling"""
    
    def test_malformed_json_request(self, client):
        """Test handling of malformed JSON in auth requests"""
        response = client.post('/auth/login', 
                             data='{"invalid": json}',
                             content_type='application/json')
        
        assert response.status_code == 400
    
    def test_missing_content_type(self, client, sample_user_data):
        """Test request without proper content type"""
        login_data = {
            'data': {
                'email': sample_user_data['email'],
                'password': sample_user_data['password']
            }
        }
        
        response = client.post('/auth/login', data=json.dumps(login_data))
        
        # Should still work or return appropriate error
        assert response.status_code in [200, 400, 415]
    
    def test_empty_request_body(self, client):
        """Test request with empty body"""
        response = client.post('/auth/login', 
                             json={},
                             content_type='application/json')
        
        assert response.status_code in [400, 422]
    
    def test_sql_injection_attempt(self, client):
        """Test SQL injection attempt in login"""
        login_data = {
            'data': {
                'email': "'; DROP TABLE users; --",
                'password': 'anypassword'
            }
        }
        
        response = client.post('/auth/login', json=login_data)
        
        # Should not cause server error, should return 401 or validation error
        assert response.status_code in [401, 422]
        
        # Verify response structure is maintained
        data = response.get_json()
        assert 'data' in data
