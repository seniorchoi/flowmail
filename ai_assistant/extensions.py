from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect  # Import CSRFProtect
from .custom_csrf import csrf  # Import the customized CSRFProtect

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
#csrf = CSRFProtect()  # Initialize CSRFProtect
