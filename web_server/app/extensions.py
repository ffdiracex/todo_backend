"""Flask extensions initialization."""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Database
db = SQLAlchemy()

# Migrations
migrate = Migrate()

# Login management
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

# Password hashing
bcrypt = Bcrypt()

# Caching
cache = Cache()

# Rate limiting
limiter = Limiter(key_func=get_remote_address)