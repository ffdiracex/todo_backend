"""Authentication forms with validation."""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Regexp, ValidationError
from app.repositories.user_repository import UserRepository

class RegistrationForm(FlaskForm):
    """User registration form."""
    
    username = StringField('Username', validators=[
        DataRequired(message='Username is required'),
        Length(min=3, max=80, message='Username must be between 3 and 80 characters'),
        Regexp(r'^[a-zA-Z0-9_]+$', message='Username can only contain letters, numbers, and underscores')
    ])
    
    email = StringField('Email', validators=[
        DataRequired(message='Email is required'),
        Email(message='Please enter a valid email address'),
        Length(max=120)
    ])
    
    full_name = StringField('Full Name', validators=[
        Length(max=100, message='Full name cannot exceed 100 characters')
    ])
    
    phone = StringField('Phone Number', validators=[
        Regexp(r'^\+?1?\d{9,15}$', message='Please enter a valid phone number')
    ])
    
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required'),
        Length(min=8, message='Password must be at least 8 characters'),
        Regexp(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$', 
               message='Password must contain at least one letter and one number')
    ])
    
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm your password'),
        EqualTo('password', message='Passwords must match')
    ])
    
    timezone = SelectField('Timezone', choices=[
        ('UTC', 'UTC'),
        ('America/New_York', 'Eastern Time'),
        ('America/Chicago', 'Central Time'),
        ('America/Denver', 'Mountain Time'),
        ('America/Los_Angeles', 'Pacific Time'),
        ('Europe/London', 'London'),
        ('Europe/Paris', 'Paris'),
        ('Asia/Tokyo', 'Tokyo'),
    ], default='UTC')
    
    def validate_username(self, field):
        """Check if username is already taken."""
        repo = UserRepository()
        if repo.exists(username=field.data):
            raise ValidationError('Username already taken. Please choose another.')
    
    def validate_email(self, field):
        """Check if email is already registered."""
        repo = UserRepository()
        if repo.exists(email=field.data):
            raise ValidationError('Email already registered. Please use another or login.')

class LoginForm(FlaskForm):
    """User login form."""
    
    username = StringField('Username', validators=[
        DataRequired(message='Username is required')
    ])
    
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required')
    ])
    
    remember_me = BooleanField('Remember Me')

class ProfileForm(FlaskForm):
    """User profile update form."""
    
    full_name = StringField('Full Name', validators=[
        Length(max=100)
    ])
    
    phone = StringField('Phone Number', validators=[
        Regexp(r'^\+?1?\d{9,15}$', message='Please enter a valid phone number')
    ])
    
    bio = TextAreaField('Bio', validators=[
        Length(max=500, message='Bio cannot exceed 500 characters')
    ])
    
    timezone = SelectField('Timezone', choices=[
        ('UTC', 'UTC'),
        ('America/New_York', 'Eastern Time'),
        ('America/Chicago', 'Central Time'),
        ('America/Denver', 'Mountain Time'),
        ('America/Los_Angeles', 'Pacific Time'),
    ])
    
    theme_preference = SelectField('Theme', choices=[
        ('light', 'Light'),
        ('dark', 'Dark'),
    ])