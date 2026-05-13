"""Complete working Todo App - Single File Version with Fixed Endpoints"""
import os
from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps

# Get the directory where this file is located
basedir = os.path.abspath(os.path.dirname(__file__))

# Initialize Flask app
app = Flask(__name__,
           template_folder=os.path.join(basedir, 'templates'),
           static_folder=os.path.join(basedir, 'static'))

app.config['SECRET_KEY'] = 'your-super-secret-key-change-this-12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'todo.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SECURE'] = False

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# Models
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        return str(self.id)

class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending', index=True)
    priority = db.Column(db.String(20), default='medium', index=True)
    due_date = db.Column(db.DateTime)
    tags = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    user = db.relationship('User', backref='tasks', lazy=True)
    
    def mark_complete(self):
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
    
    def is_overdue(self):
        if self.due_date and self.status != 'completed':
            return datetime.utcnow() > self.due_date
        return False

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        
        errors = []
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters long.')
        if not email or '@' not in email:
            errors.append('Please enter a valid email address.')
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters long.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        
        if User.query.filter_by(username=username).first():
            errors.append('Username already exists.')
        if User.query.filter_by(email=email).first():
            errors.append('Email already registered.')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email, full_name=full_name, phone=phone)
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Registration failed: {str(e)}', 'danger')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password')
        remember = request.form.get('remember_me') == 'on'
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated.', 'danger')
                return redirect(url_for('login'))
            
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            flash(f'Welcome back, {user.username}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/home')
@login_required
def home():
    status_filter = request.args.get('status', '')
    priority_filter = request.args.get('priority', '')
    
    query = Task.query.filter_by(user_id=current_user.id)
    if status_filter:
        query = query.filter_by(status=status_filter)
    if priority_filter:
        query = query.filter_by(priority=priority_filter)
    
    tasks = query.order_by(Task.priority.desc(), Task.due_date.asc(), Task.created_at.desc()).all()
    
    pending_tasks = [t for t in tasks if t.status == 'pending']
    completed_tasks = [t for t in tasks if t.status == 'completed']
    overdue_tasks = [t for t in pending_tasks if t.is_overdue()]
    
    stats = {
        'total': len(tasks),
        'pending': len(pending_tasks),
        'completed': len(completed_tasks),
        'overdue': len(overdue_tasks),
        'completion_rate': (len(completed_tasks) / len(tasks) * 100) if tasks else 0
    }
    
    return render_template('home.html', 
                         user=current_user,
                         pending_tasks=pending_tasks,
                         completed_tasks=completed_tasks,
                         overdue_tasks=overdue_tasks,
                         stats=stats)

@app.route('/add_task', methods=['POST'])
@login_required
def add_task():
    title = request.form.get('title', '').strip()
    if not title:
        flash('Task title is required!', 'danger')
        return redirect(url_for('home'))
    
    due_date = None
    due_date_str = request.form.get('due_date')
    if due_date_str:
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
        except ValueError:
            flash('Invalid date format. Use YYYY-MM-DD.', 'warning')
    
    task = Task(
        title=title,
        description=request.form.get('description', '').strip(),
        priority=request.form.get('priority', 'medium'),
        due_date=due_date,
        tags=request.form.get('tags', '').strip(),
        user_id=current_user.id
    )
    
    try:
        db.session.add(task)
        db.session.commit()
        flash('Task added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to add task: {str(e)}', 'danger')
    
    return redirect(url_for('home'))

@app.route('/complete_task/<int:task_id>')
@login_required
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('home'))
    
    task.mark_complete()
    db.session.commit()
    flash('Task marked as completed!', 'success')
    return redirect(url_for('home'))

@app.route('/delete_task/<int:task_id>')
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('home'))
    
    try:
        db.session.delete(task)
        db.session.commit()
        flash('Task deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to delete task: {str(e)}', 'danger')
    
    return redirect(url_for('home'))

@app.route('/edit_task/<int:task_id>', methods=['POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('home'))
    
    title = request.form.get('title', '').strip()
    if not title:
        flash('Task title is required!', 'danger')
        return redirect(url_for('home'))
    
    task.title = title
    task.description = request.form.get('description', '').strip()
    task.priority = request.form.get('priority', 'medium')
    task.tags = request.form.get('tags', '').strip()
    
    due_date_str = request.form.get('due_date')
    if due_date_str:
        try:
            task.due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
        except ValueError:
            flash('Invalid date format. Use YYYY-MM-DD.', 'warning')
    else:
        task.due_date = None
    
    task.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        flash('Task updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to update task: {str(e)}', 'danger')
    
    return redirect(url_for('home'))

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    full_name = request.form.get('full_name', '').strip()
    phone = request.form.get('phone', '').strip()
    
    current_user.full_name = full_name
    current_user.phone = phone
    
    try:
        db.session.commit()
        flash('Profile updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to update profile: {str(e)}', 'danger')
    
    return redirect(url_for('profile'))

@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not current_user.check_password(current_password):
        flash('Current password is incorrect.', 'danger')
        return redirect(url_for('profile'))
    
    if len(new_password) < 6:
        flash('New password must be at least 6 characters long.', 'danger')
        return redirect(url_for('profile'))
    
    if new_password != confirm_password:
        flash('New passwords do not match.', 'danger')
        return redirect(url_for('profile'))
    
    current_user.set_password(new_password)
    
    try:
        db.session.commit()
        flash('Password changed successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to change password: {str(e)}', 'danger')
    
    return redirect(url_for('profile'))

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# Create database tables
with app.app_context():
    # Create instance directory if it doesn't exist
    instance_path = os.path.join(basedir, 'instance')
    os.makedirs(instance_path, exist_ok=True)
    
    # Create tables
    db.create_all()
    print("✅ Database created successfully!")
    
    # Create admin user if not exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@example.com',
            full_name='Administrator',
            is_admin=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin user created (username: admin, password: admin123)")

if __name__ == '__main__':
    print("\n" + "!"*60)
    print("starting...")
    print("!"*60)
    print(f" Server will run at: http://localhost:5000")
    print(f" Admin login: admin / admin123")
    print(f" Templates folder: {os.path.join(basedir, 'templates')}")
    print("!"*60 + "\n")
    app.run(debug=True, host='127.0.0.1', port=5000)