"""User model."""
from datetime import datetime
from flask_login import UserMixin
from typing import Optional, List
from .base import BaseModel
from app.extensions import db, bcrypt

class User(BaseModel, UserMixin):
    """User model with authentication and profile management."""
    
    __tablename__ = 'users'
    
    # Basic info
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    
    # Authentication
    password_hash = db.Column(db.String(128), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    email_verified = db.Column(db.Boolean, default=False)
    
    # Profile
    avatar_url = db.Column(db.String(200))
    bio = db.Column(db.Text)
    timezone = db.Column(db.String(50), default='UTC')
    theme_preference = db.Column(db.String(20), default='light')
    
    # Security
    last_login = db.Column(db.DateTime)
    login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)
    
    # Relationships
    tasks = db.relationship('Task', back_populates='owner', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, username: str, email: str, password: str, **kwargs):
        """Initialize user with hashed password."""
        self.username = username
        self.email = email
        self.set_password(password)
        super().__init__(**kwargs)
    
    def set_password(self, password: str) -> None:
        """Hash and set password."""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password: str) -> bool:
        """Verify password."""
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def increment_login_attempts(self) -> None:
        """Increment failed login attempts."""
        self.login_attempts += 1
        if self.login_attempts >= 5:
            from datetime import timedelta
            self.locked_until = datetime.utcnow() + timedelta(minutes=15)
        db.session.commit()
    
    def reset_login_attempts(self) -> None:
        """Reset login attempts."""
        self.login_attempts = 0
        self.locked_until = None
        db.session.commit()
    
    def is_locked(self) -> bool:
        """Check if account is locked."""
        if self.locked_until and datetime.utcnow() < self.locked_until:
            return True
        return False
    
    @property
    def task_count(self) -> int:
        """Get total task count."""
        return self.tasks.count()
    
    @property
    def pending_tasks_count(self) -> int:
        """Get pending tasks count."""
        return self.tasks.filter_by(status='pending').count()
    
    @property
    def completed_tasks_count(self) -> int:
        """Get completed tasks count."""
        return self.tasks.filter_by(status='completed').count()
    
    def to_dict(self, include_private: bool = False) -> dict:
        """Convert user to dictionary."""
        data = super().to_dict()
        if not include_private:
            data.pop('password_hash', None)
            data.pop('login_attempts', None)
            data.pop('locked_until', None)
        return data
    
    def __repr__(self) -> str:
        return f'<User {self.username}>'