from typing import Optional, Dict, Any
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
from flask_bcrypt import generate_password_hash, check_password_hash

from .models import User, db


class UserService:
    """Service class for user-related business logic"""

    def get_all_users(self) -> list[User]:
        """
        Get all users
        
        Returns:
            List of User objects
        """
        try:
            return User.query.all()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error in get_all_users: {str(e)}")
            return []
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Get user by ID
        
        Args:
            user_id: UUID string of the user
            
        Returns:
            User object if found, None otherwise
        """
        try:
            return User.query.filter_by(id=user_id).first()
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error in get_user_by_id: {str(e)}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address
        
        Args:
            email: Email address of the user
            
        Returns:
            User object if found, None otherwise
        """
        try:
            return User.query.filter_by(email=email.lower()).first()
        except SQLAlchemyError as e:
            print(f"Database error in get_user_by_email: {str(e)}")
            return None
    
    def create_user(self, user_data: Dict[str, Any]) -> Optional[User]:
        """
        Create a new user
        
        Args:
            user_data: Dictionary containing user information
                - email: User's email address
                - password: Plain text password
                - full_name: User's full name
                - role: User role (optional, defaults to 'camp_manager')
                
        Returns:
            Created User object if successful, None otherwise
            
        Raises:
            ValueError: If required fields are missing or invalid
        """
        try:
            # Validate required fields
            required_fields = ['email', 'password', 'full_name']
            for field in required_fields:
                if field not in user_data or not user_data[field]:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate email format (basic check)
            email = user_data['email'].lower().strip()
            if '@' not in email or '.' not in email.split('@')[1]:
                raise ValueError("Invalid email format")
            
            # Validate password strength
            password = user_data['password']
            if len(password) < 8:
                raise ValueError("Password must be at least 8 characters long")
            
            # Validate full name
            full_name = user_data['full_name'].strip()
            if len(full_name) < 2:
                raise ValueError("Full name must be at least 2 characters long")
            
            # Check if user already exists
            existing_user = self.get_user_by_email(email)
            if existing_user:
                raise ValueError("User with this email already exists")
            
            # Create new user
            new_user = User(
                email=email,
                full_name=full_name,
                role=user_data.get('role', 'camp_manager')
            )
            
            # Set password (this will hash it)
            new_user.set_password(password)
            
            # Save to database
            db.session.add(new_user)
            db.session.commit()
            
            current_app.logger.info(f"New user created: {email}")
            return new_user
            
        except ValueError:
            # Re-raise validation errors
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in create_user: {str(e)}")
            raise Exception("Failed to create user due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in create_user: {str(e)}")
            raise Exception("Failed to create user")
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate user with email and password
        
        Args:
            email: User's email address
            password: Plain text password
            
        Returns:
            User object if authentication successful, None otherwise
        """
        try:
            if not email or not password:
                return None
            
            # Get user by email
            user = self.get_user_by_email(email.lower().strip())
            if not user:
                current_app.logger.warning(f"Authentication failed: User not found for email {email}")
                return None
            
            # Check password
            if not user.check_password(password):
                current_app.logger.warning(f"Authentication failed: Invalid password for email {email}")
                return None
            
            current_app.logger.info(f"User authenticated successfully: {email}")
            return user
            
        except Exception as e:
            current_app.logger.error(f"Error in authenticate_user: {str(e)}")
            return None
    
    def update_user(self, user_id: str, update_data: Dict[str, Any]) -> Optional[User]:
        """
        Update user information
        
        Args:
            user_id: UUID string of the user to update
            update_data: Dictionary containing fields to update
                - email: New email address (optional)
                - full_name: New full name (optional)
                - role: New role (optional)
                
        Returns:
            Updated User object if successful, None otherwise
            
        Raises:
            ValueError: If validation fails
        """
        try:
            # Get user
            user = self.get_user_by_id(user_id)
            if not user:
                return None
            
            # Validate and update email if provided
            if 'email' in update_data:
                new_email = update_data['email'].lower().strip()
                
                # Basic email validation
                if '@' not in new_email or '.' not in new_email.split('@')[1]:
                    raise ValueError("Invalid email format")
                
                # Check if email is already taken by another user
                existing_user = self.get_user_by_email(new_email)
                if existing_user and str(existing_user.id) != user_id:
                    raise ValueError("Email already exists")
                
                user.email = new_email
            
            # Validate and update full name if provided
            if 'full_name' in update_data:
                full_name = update_data['full_name'].strip()
                if len(full_name) < 2:
                    raise ValueError("Full name must be at least 2 characters long")
                user.full_name = full_name
            
            # Update role if provided
            if 'role' in update_data:
                role = update_data['role']
                if role not in ['camp_manager', 'volunteer']:
                    raise ValueError("Invalid role. Must be 'camp_manager' or 'volunteer'")
                user.role = role
            
            # Save changes
            db.session.commit()
            
            current_app.logger.info(f"User updated successfully: {user.email}")
            return user
            
        except ValueError:
            # Re-raise validation errors
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in update_user: {str(e)}")
            raise Exception("Failed to update user due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in update_user: {str(e)}")
            raise Exception("Failed to update user")
    
    def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """
        Change user password
        
        Args:
            user_id: UUID string of the user
            current_password: Current plain text password
            new_password: New plain text password
            
        Returns:
            True if password changed successfully, False otherwise
            
        Raises:
            ValueError: If validation fails
        """
        try:
            # Get user
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            # Verify current password
            if not user.check_password(current_password):
                current_app.logger.warning(f"Password change failed: Invalid current password for user {user.email}")
                return False
            
            # Validate new password
            if len(new_password) < 8:
                raise ValueError("New password must be at least 8 characters long")
            
            # Check if new password is different from current
            if check_password_hash(user.password_hash, new_password):
                raise ValueError("New password must be different from current password")
            
            # Set new password
            user.set_password(new_password)
            
            # Save changes
            db.session.commit()
            
            current_app.logger.info(f"Password changed successfully for user: {user.email}")
            return True
            
        except ValueError:
            # Re-raise validation errors
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in change_password: {str(e)}")
            raise Exception("Failed to change password due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in change_password: {str(e)}")
            raise Exception("Failed to change password")
    
    def delete_user(self, user_id: str) -> bool:
        """
        Delete a user (soft delete by setting inactive flag or hard delete)
        
        Args:
            user_id: UUID string of the user to delete
            
        Returns:
            True if user deleted successfully, False otherwise
        """
        try:
            # Get user
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            # Hard delete - remove from database
            # Note: This will cascade delete related camps, expenses, etc.
            # Consider implementing soft delete if you need to preserve data
            db.session.delete(user)
            db.session.commit()
            
            current_app.logger.info(f"User deleted successfully: {user.email}")
            return True
            
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in delete_user: {str(e)}")
            raise Exception("Failed to delete user due to database error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in delete_user: {str(e)}")
            raise Exception("Failed to delete user")
    
    def get_users_by_role(self, role: str) -> list[User]:
        """
        Get all users with a specific role
        
        Args:
            role: Role to filter by ('camp_manager' or 'volunteer')
            
        Returns:
            List of User objects
        """
        try:
            if role not in ['camp_manager', 'volunteer']:
                raise ValueError("Invalid role")
            
            return User.query.filter_by(role=role).all()
            
        except SQLAlchemyError as e:
            current_app.logger.error(f"Database error in get_users_by_role: {str(e)}")
            return []
        except Exception as e:
            current_app.logger.error(f"Unexpected error in get_users_by_role: {str(e)}")
            return []
    
    def get_user_stats(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get statistics for a user (camps managed, registrations, etc.)
        
        Args:
            user_id: UUID string of the user
            
        Returns:
            Dictionary containing user statistics, None if user not found
        """
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return None
            
            # Count camps managed (if camp_manager)
            camps_count = len(user.camps) if user.role == 'camp_manager' else 0
            
            # Count total registrations across all camps
            total_registrations = 0
            total_revenue = 0
            active_camps = 0
            
            if user.role == 'camp_manager':
                for camp in user.camps:
                    if camp.is_active:
                        active_camps += 1
                    
                    camp_registrations = len(camp.registrations)
                    total_registrations += camp_registrations
                    
                    # Calculate revenue from paid registrations
                    for registration in camp.registrations:
                        if registration.has_paid:
                            total_revenue += float(registration.total_amount)
            
            # Safely handle datetime serialization - commented out to avoid isoformat errors
            member_since_str = str(user.created_at) if user.created_at else None
            
            # member_since_str = None
            # if user.created_at:
            #     if hasattr(user.created_at, 'isoformat'):
            #         member_since_str = user.created_at.isoformat()
            #     else:
            #         member_since_str = str(user.created_at)
            
            return {
                'user_id': str(user.id),
                'role': user.role,
                'camps_managed': camps_count,
                'active_camps': active_camps,
                'total_registrations': total_registrations,
                'total_revenue': float(total_revenue),
                'member_since': member_since_str
            }
            
        except Exception as e:
            current_app.logger.error(f"Error in get_user_stats: {str(e)}")
            return None
    
    def validate_user_permissions(self, user_id: str, required_role: str = None) -> bool:
        """
        Validate user permissions for specific actions
        
        Args:
            user_id: UUID string of the user
            required_role: Required role for the action (optional)
            
        Returns:
            True if user has required permissions, False otherwise
        """
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            # If no specific role required, just check if user exists
            if not required_role:
                return True
            
            # Check if user has required role
            if required_role == 'camp_manager' and user.role != 'camp_manager':
                return False
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error in validate_user_permissions: {str(e)}")
            return False
