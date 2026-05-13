"""User repository with specialized queries."""
from typing import Optional, List
from app.models.user import User
from app.repositories.base_repository import BaseRepository

class UserRepository(BaseRepository[User]):
    """Repository for User model with additional methods."""
    
    def __init__(self):
        super().__init__(User)
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return User.query.filter_by(username=username).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return User.query.filter_by(email=email).first()
    
    def get_active_users(self, page: int = 1, per_page: int = 20):
        """Get all active users."""
        return User.query.filter_by(is_active=True).paginate(
            page=page, per_page=per_page, error_out=False
        )
    
    def get_admin_users(self) -> List[User]:
        """Get all admin users."""
        return User.query.filter_by(is_admin=True).all()
    
    def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate user by username and password."""
        user = self.get_by_username(username)
        if user and not user.is_locked() and user.check_password(password):
            user.reset_login_attempts()
            return user
        elif user:
            user.increment_login_attempts()
        return None
    
    def create_admin(self, username: str, email: str, password: str) -> Optional[User]:
        """Create an admin user."""
        if self.exists(username=username) or self.exists(email=email):
            return None
        return self.create(
            username=username,
            email=email,
            password=password,
            is_admin=True,
            email_verified=True
        )
    
    def update_last_login(self, user_id: int) -> None:
        """Update user's last login timestamp."""
        from datetime import datetime
        self.update(user_id, last_login=datetime.utcnow())
    
    def verify_email(self, user_id: int) -> None:
        """Mark user's email as verified."""
        self.update(user_id, email_verified=True)
    
    def lock_account(self, user_id: int) -> None:
        """Lock user account."""
        from datetime import datetime, timedelta
        self.update(user_id, locked_until=datetime.utcnow() + timedelta(hours=24))
    
    def unlock_account(self, user_id: int) -> None:
        """Unlock user account."""
        self.update(user_id, locked_until=None, login_attempts=0)