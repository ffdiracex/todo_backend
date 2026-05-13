"""Authentication API routes."""
from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.services.auth_service import AuthService
from app.forms.auth_forms import RegistrationForm, LoginForm, ProfileForm
from app.extensions import limiter
import logging

# Set up logging
logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)
auth_service = AuthService()

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Register a new user - handles both GET and POST requests."""
    
    # GET request - just show the form (though we usually use web_bp for this)
    if request.method == 'GET':
        form = RegistrationForm()
        return render_template('register.html', form=form)
    
    # POST request - process registration
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    # Handle form data (supports both JSON and form-urlencoded)
    if request.is_json:
        form_data = request.get_json()
        form = RegistrationForm(data=form_data)
    else:
        form = RegistrationForm()
    
    # Validate form
    if not form.validate_on_submit():
        logger.warning(f"Registration validation failed: {form.errors}")
        
        if is_ajax or request.is_json:
            return jsonify({
                'success': False,
                'errors': form.errors,
                'message': 'Validation failed'
            }), 400
        else:
            # Traditional form submission - flash errors and redirect back
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{field}: {error}', 'danger')
            return redirect(url_for('web.register_page'))
    
    # Attempt to register user
    user, error = auth_service.register_user(form.data)
    
    if error:
        logger.error(f"Registration failed: {error}")
        
        if is_ajax or request.is_json:
            return jsonify({
                'success': False,
                'error': error,
                'message': 'Registration failed'
            }), 400
        else:
            flash(error, 'danger')
            return redirect(url_for('web.register_page'))
    
    # Registration successful
    logger.info(f"New user registered: {user['username']} ({user['email']})")
    
    if is_ajax or request.is_json:
        return jsonify({
            'success': True,
            'user': user,
            'message': 'Registration successful! Please login.'
        }), 201
    else:
        flash('Registration successful! Please login to continue.', 'success')
        return redirect(url_for('web.login_page'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login user - handles both GET and POST requests."""
    
    # GET request - show login form
    if request.method == 'GET':
        form = LoginForm()
        return render_template('login.html', form=form)
    
    # POST request - process login
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    # Handle form data
    if request.is_json:
        form_data = request.get_json()
        form = LoginForm(data=form_data)
    else:
        form = LoginForm()
    
    # Validate form
    if not form.validate_on_submit():
        logger.warning(f"Login validation failed: {form.errors}")
        
        if is_ajax or request.is_json:
            return jsonify({
                'success': False,
                'errors': form.errors,
                'message': 'Validation failed'
            }), 400
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(error, 'danger')
            return redirect(url_for('web.login_page'))
    
    # Attempt to authenticate user
    user, error = auth_service.login_user(
        form.username.data,
        form.password.data,
        form.remember_me.data if hasattr(form, 'remember_me') else False
    )
    
    if error:
        logger.warning(f"Login failed for user {form.username.data}: {error}")
        
        if is_ajax or request.is_json:
            return jsonify({
                'success': False,
                'error': error,
                'message': 'Login failed'
            }), 401
        else:
            flash(error, 'danger')
            return redirect(url_for('web.login_page'))
    
    # Login successful
    logger.info(f"User logged in: {user['username']} (ID: {user['id']})")
    
    # Check if there's a next URL to redirect to
    next_url = session.pop('next_url', None)
    if next_url and not is_ajax:
        response = redirect(next_url)
    elif is_ajax or request.is_json:
        response = jsonify({
            'success': True,
            'user': user,
            'message': f'Welcome back, {user["username"]}!',
            'redirect': url_for('web.home')
        }), 200
    else:
        flash(f'Welcome back, {user["username"]}!', 'success')
        response = redirect(url_for('web.home'))
    
    return response

@auth_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    """Logout user."""
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    username = current_user.username
    
    auth_service.logout_user()
    logger.info(f"User logged out: {username}")
    
    if is_ajax or request.is_json:
        return jsonify({
            'success': True,
            'message': 'Logged out successfully',
            'redirect': url_for('web.login_page')
        }), 200
    else:
        flash('You have been logged out successfully.', 'info')
        return redirect(url_for('web.login_page'))

@auth_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """Get user profile."""
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    profile = auth_service.get_user_profile(current_user.id)
    
    if profile:
        if is_ajax or request.is_json:
            return jsonify({
                'success': True,
                'profile': profile
            }), 200
        else:
            # If not AJAX, render a profile page (you may want to create this template)
            return render_template('profile.html', user=profile)
    
    error_msg = 'Profile not found'
    if is_ajax or request.is_json:
        return jsonify({
            'success': False,
            'error': error_msg
        }), 404
    else:
        flash(error_msg, 'danger')
        return redirect(url_for('web.home'))

@auth_bp.route('/profile', methods=['PUT', 'POST'])
@login_required
def update_profile():
    """Update user profile."""
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    # Handle both JSON and form data
    if request.is_json:
        form_data = request.get_json()
    else:
        form_data = request.form.to_dict()
    
    # Handle file upload for avatar
    if 'avatar' in request.files:
        avatar_file = request.files['avatar']
        if avatar_file and avatar_file.filename:
            # Process avatar upload (you'd implement this in auth_service)
            form_data['avatar_url'] = f"/uploads/avatars/{current_user.id}.jpg"
    
    # Validate with form if needed
    form = ProfileForm(data=form_data)
    if form.validate():
        success, message = auth_service.update_user_profile(current_user.id, form_data)
    else:
        success = False
        message = "Validation failed"
    
    if success:
        logger.info(f"Profile updated for user {current_user.username}")
        
        if is_ajax or request.is_json:
            return jsonify({
                'success': True,
                'message': message
            }), 200
        else:
            flash(message, 'success')
            return redirect(url_for('web.home'))
    else:
        if is_ajax or request.is_json:
            return jsonify({
                'success': False,
                'error': message,
                'errors': form.errors if 'form' in locals() else None
            }), 400
        else:
            flash(message or 'Failed to update profile', 'danger')
            return redirect(url_for('web.home'))

@auth_bp.route('/change-password', methods=['POST'])
@login_required
@limiter.limit("5 per hour")
def change_password():
    """Change user password."""
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    # Get data from request
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()
    
    # Validate required fields
    if not data or 'old_password' not in data or 'new_password' not in data:
        error_msg = 'Missing required fields: old_password and new_password'
        
        if is_ajax or request.is_json:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        else:
            flash(error_msg, 'danger')
            return redirect(url_for('web.home'))
    
    # Validate new password strength
    if len(data['new_password']) < 8:
        error_msg = 'New password must be at least 8 characters long'
        if is_ajax or request.is_json:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        else:
            flash(error_msg, 'danger')
            return redirect(url_for('web.home'))
    
    # Attempt to change password
    success, message = auth_service.change_password(
        current_user.id,
        data['old_password'],
        data['new_password']
    )
    
    if success:
        logger.info(f"Password changed for user {current_user.username}")
        
        if is_ajax or request.is_json:
            return jsonify({
                'success': True,
                'message': message
            }), 200
        else:
            flash(message, 'success')
            return redirect(url_for('web.home'))
    else:
        if is_ajax or request.is_json:
            return jsonify({
                'success': False,
                'error': message
            }), 400
        else:
            flash(message, 'danger')
            return redirect(url_for('web.home'))

@auth_bp.route('/reset-password-request', methods=['POST'])
@limiter.limit("3 per hour")
def reset_password_request():
    """Request password reset."""
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    # Get email from request
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()
    
    if not data or 'email' not in data:
        error_msg = 'Email is required'
        
        if is_ajax or request.is_json:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        else:
            flash(error_msg, 'danger')
            return redirect(url_for('web.login_page'))
    
    success, message = auth_service.reset_password_request(data['email'])
    
    if is_ajax or request.is_json:
        return jsonify({
            'success': success,
            'message': message
        }), 200 if success else 400
    else:
        flash(message, 'success' if success else 'danger')
        return redirect(url_for('web.login_page'))

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
@limiter.limit("5 per hour")
def reset_password():
    """Reset password with token."""
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    # GET request - show reset password form
    if request.method == 'GET':
        token = request.args.get('token')
        if not token:
            flash('Invalid or missing reset token', 'danger')
            return redirect(url_for('web.login_page'))
        
        # Render reset password form
        return render_template('reset_password.html', token=token)
    
    # POST request - process password reset
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()
    
    if not data or 'token' not in data or 'new_password' not in data:
        error_msg = 'Token and new password are required'
        
        if is_ajax or request.is_json:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        else:
            flash(error_msg, 'danger')
            return redirect(url_for('web.login_page'))
    
    # Validate new password strength
    if len(data['new_password']) < 8:
        error_msg = 'Password must be at least 8 characters long'
        if is_ajax or request.is_json:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        else:
            flash(error_msg, 'danger')
            return redirect(url_for('web.login_page'))
    
    success, message = auth_service.reset_password(data['token'], data['new_password'])
    
    if success:
        logger.info(f"Password reset successfully for user")
        
        if is_ajax or request.is_json:
            return jsonify({
                'success': True,
                'message': message
            }), 200
        else:
            flash(message, 'success')
            return redirect(url_for('web.login_page'))
    else:
        if is_ajax or request.is_json:
            return jsonify({
                'success': False,
                'error': message
            }), 400
        else:
            flash(message, 'danger')
            return redirect(url_for('web.login_page'))

@auth_bp.route('/verify-email/<token>', methods=['GET'])
@limiter.limit("10 per hour")
def verify_email(token):
    """Verify user email address."""
    from flask import current_app
    import jwt
    
    try:
        # Decode the token
        payload = jwt.decode(
            token,
            current_app.config['SECRET_KEY'],
            algorithms=['HS256']
        )
        
        user_id = payload.get('user_id')
        if user_id:
            # Mark email as verified
            from app.repositories.user_repository import UserRepository
            repo = UserRepository()
            success = repo.verify_email(user_id)
            
            if success:
                flash('Email verified successfully! You can now login.', 'success')
            else:
                flash('Email verification failed. Please contact support.', 'danger')
        else:
            flash('Invalid verification token.', 'danger')
            
    except jwt.ExpiredSignatureError:
        flash('Verification token has expired. Please request a new one.', 'warning')
    except jwt.InvalidTokenError:
        flash('Invalid verification token.', 'danger')
    
    return redirect(url_for('web.login_page'))

@auth_bp.route('/resend-verification', methods=['POST'])
@login_required
@limiter.limit("2 per hour")
def resend_verification():
    """Resend email verification link."""
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if current_user.email_verified:
        message = 'Email already verified'
        if is_ajax or request.is_json:
            return jsonify({
                'success': False,
                'error': message
            }), 400
        else:
            flash(message, 'warning')
            return redirect(url_for('web.home'))
    
    # Generate verification token
    import jwt
    from flask import current_app
    from datetime import datetime, timedelta
    
    token = jwt.encode(
        {
            'user_id': current_user.id,
            'email': current_user.email,
            'exp': datetime.utcnow() + timedelta(hours=24)
        },
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )
    
    # Send verification email
    verification_url = url_for('auth.verify_email', token=token, _external=True)
    
    # Here you would send the email (using email_service)
    # For now, just log it
    logger.info(f"Verification email sent to {current_user.email}: {verification_url}")
    
    message = 'Verification email sent. Please check your inbox.'
    
    if is_ajax or request.is_json:
        return jsonify({
            'success': True,
            'message': message
        }), 200
    else:
        flash(message, 'info')
        return redirect(url_for('web.home'))

@auth_bp.route('/check-auth', methods=['GET'])
@login_required
def check_auth():
    """Check if user is authenticated (for frontend checks)."""
    return jsonify({
        'authenticated': True,
        'user': {
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email,
            'is_admin': current_user.is_admin
        }
    }), 200

@auth_bp.route('/csrf-token', methods=['GET'])
@login_required
def get_csrf_token():
    """Get CSRF token for AJAX requests."""
    from flask_wtf.csrf import generate_csrf
    return jsonify({
        'csrf_token': generate_csrf()
    }), 200

@auth_bp.errorhandler(429)
def ratelimit_error(error):
    """Handle rate limit errors."""
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    message = 'Too many requests. Please try again later.'
    
    if is_ajax or request.is_json:
        return jsonify({
            'success': False,
            'error': message
        }), 429
    else:
        flash(message, 'danger')
        return redirect(url_for('web.home'))

@auth_bp.errorhandler(401)
def unauthorized_error(error):
    """Handle unauthorized errors."""
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if is_ajax or request.is_json:
        return jsonify({
            'success': False,
            'error': 'Unauthorized. Please login.',
            'redirect': url_for('web.login_page')
        }), 401
    else:
        flash('Please login to access this page.', 'warning')
        return redirect(url_for('web.login_page'))

@auth_bp.errorhandler(403)
def forbidden_error(error):
    """Handle forbidden errors."""
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if is_ajax or request.is_json:
        return jsonify({
            'success': False,
            'error': 'Access forbidden. You don\'t have permission for this action.'
        }), 403
    else:
        flash('You don\'t have permission to access this page.', 'danger')
        return redirect(url_for('web.home'))

@auth_bp.errorhandler(404)
def not_found_error(error):
    """Handle not found errors."""
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if is_ajax or request.is_json:
        return jsonify({
            'success': False,
            'error': 'Resource not found'
        }), 404
    else:
        flash('Page not found.', 'danger')
        return redirect(url_for('web.home'))

@auth_bp.route('/session-info', methods=['GET'])
@login_required
def session_info():
    """Get current session information."""
    return jsonify({
        'session_id': session.get('_id', 'unknown'),
        'user_id': session.get('user_id'),
        'username': session.get('username'),
        'is_admin': session.get('is_admin', False),
        'session_lifetime': current_user.get_id() if current_user.is_authenticated else None
    }), 200