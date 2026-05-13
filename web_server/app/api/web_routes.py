"""Web routes for rendering HTML templates."""
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.forms.auth_forms import RegistrationForm, LoginForm

web_bp = Blueprint('web', __name__)

@web_bp.route('/')
def index():
    """Home page."""
    if current_user.is_authenticated:
        return redirect(url_for('web.home'))
    return redirect(url_for('web.login_page'))

@web_bp.route('/home')
@login_required
def home():
    """Main todo app page."""
    return render_template('home.html', user=current_user)

@web_bp.route('/register')
def register_page():
    """Registration page."""
    if current_user.is_authenticated:
        return redirect(url_for('web.home'))
    form = RegistrationForm()
    return render_template('register.html', form=form)

@web_bp.route('/login')
def login_page():
    """Login page."""
    if current_user.is_authenticated:
        return redirect(url_for('web.home'))
    form = LoginForm()
    return render_template('login.html', form=form)