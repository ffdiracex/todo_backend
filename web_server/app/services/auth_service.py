"""Authentication service with business logic."""
from typing import Optional, Dict, Any
from datetime import datetime
from flask import session
from app.repositories.user_repository import UserRepository
from app.services.email_service import EmailService
import asyncio

class AuthService:
    """Service for handling authentication logic."""
    
    def __init__(self):
        self.user_repo = UserRepository()
        self.email_service = EmailService()
    
    def register_user(self, form_data: Dict[str, Any]) -> tuple[Optional[Dict], Optional[str]]:
        """Register a new user."""
        try:
            # Check if user exists
            if self.user_repo.exists(username=form_data['username']):
                return None, 'Username already taken'
            
            if self.user_repo.exists(email=form_data['email']):
                return None, 'Email already registered'
            
            # Create user
            user = self.user_repo.create(
                username=form_data['username'],
                email=form_data['email'],
                password=form_data['password'],
                full_name=form_data.get('full_name'),
                phone=form_data.get('phone'),
                timezone=form_data.get('timezone', 'UTC')
            )
            
            # Send welcome email asynchronously
            asyncio.create_task(
                self.email_service.send_welcome_email(user.email, user.username)
            )
            
            return user.to_dict(), None
            
        except Exception as e:
            return None, f'Registration failed: {str(e)}'
    
    def login_user(self, username: str, password: str, remember: bool = False) -> tuple[Optional[Dict], Optional[str]]:
        """Authenticate and login user."""
        user = self.user_repo.authenticate(username, password)
        
        if not user:
            return None, 'Invalid username or password'
        
        if not user.is_active:
            return None, 'Account is deactivated'
        
        if user.is_locked():
            return None, 'Account is locked. Please try again later.'
        
        # Update last login
        self.user_repo.update_last_login(user.id)
        
        # Setup session
        session['user_id'] = user.id
        session['username'] = user.username
        session['is_admin'] = user.is_admin
        session.permanent = remember
        
        return user.to_dict(), None
    
    def logout_user(self) -> None:
        """Logout user and clear session."""
        session.clear()
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> tuple[bool, str]:
        """Change user password."""
        user = self.user_repo.get_by_id(user_id)
        
        if not user:
            return False, 'User not found'
        
        if not user.check_password(old_password):
            return False, 'Current password is incorrect'
        
        user.set_password(new_password)
        user.save()
        
        return True, 'Password changed successfully'
    
    def reset_password_request(self, email: str) -> tuple[bool, str]:
        """Request password reset."""
        user = self.user_repo.get_by_email(email)
        
        if not user:
            return False, 'Email not found'
        
        import jwt
        import os
        
        token = jwt.encode(
            {'user_id': user.id, 'exp': datetime.utcnow().timestamp() + 3600},
            os.environ.get('SECRET_KEY', 'secret'),
            algorithm='HS256'
        )
        
        # Send reset email asynchronously
        asyncio.create_task(
            self.email_service.send_password_reset_email(user.email, token)
        )
        
        return True, 'Password reset email sent'
    
    def reset_password(self, token: str, new_password: str) -> tuple[bool, str]:
        """Reset password using token."""
        try:
            import jwt
            import os
            
            payload = jwt.decode(
                token,
                os.environ.get('SECRET_KEY', 'secret'),
                algorithms=['HS256']
            )
            
            user = self.user_repo.get_by_id(payload['user_id'])
            if not user:
                return False, 'Invalid token'
            
            user.set_password(new_password)
            user.save()
            
            return True, 'Password reset successfully'
            
        except jwt.ExpiredSignatureError:
            return False, 'Reset token has expired'
        except jwt.InvalidTokenError:
            return False, 'Invalid reset token'
    
    def get_user_profile(self, user_id: int) -> Optional[Dict]:
        """Get user profile data."""
        user = self.user_repo.get_by_id(user_id)
        if user:
            return user.to_dict(include_private=False)
        return None
    
    def update_user_profile(self, user_id: int, profile_data: Dict) -> tuple[bool, str]:
        """Update user profile."""
        allowed_fields = ['full_name', 'phone', 'bio', 'timezone', 'theme_preference']
        update_data = {k: v for k, v in profile_data.items() if k in allowed_fields and v}
        
        if update_data:
            user = self.user_repo.update(user_id, **update_data)
            if user:
                return True, 'Profile updated successfully'
        
        return False, 'No changes made'