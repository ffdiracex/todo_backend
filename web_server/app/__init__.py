"""Flask application factory."""
from flask import Flask
from .config import Config
from .extensions import db, migrate, login_manager, bcrypt, cache, limiter

def create_app(config_class=Config):
    """Application factory pattern."""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)
    
    # Import models
    from .models.user import User
    from .models.task import Task
    
    # Setup user loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from app.repositories.user_repository import UserRepository
        repo = UserRepository()
        return repo.get_by_id(int(user_id))
    
    @login_manager.unauthorized_handler
    def unauthorized():
        from flask import redirect, url_for, flash
        flash('Please login to access this page.', 'warning')
        return redirect(url_for('web.login_page'))
    
    # Register blueprints
    from .api.web_routes import web_bp
    from .api.auth_routes import auth_bp
    from .api.task_routes import task_bp
    
    app.register_blueprint(web_bp)
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(task_bp, url_prefix='/api/tasks')
    
    # Create tables
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")
    
    return app