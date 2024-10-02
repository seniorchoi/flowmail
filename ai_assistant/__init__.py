# ai_assistant/__init__.py
import os
from flask import Flask
from .extensions import db, migrate, login_manager, csrf
from .config import DevelopmentConfig, ProductionConfig
from .auth.routes import auth_bp
from .main.routes import main_bp
from .email_handler.routes import email_handler_bp
from .webhooks.routes import webhooks_bp
from .models import User
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

#import logging
#logging.basicConfig(level=logging.INFO)

def create_app(config_class=None):
    app = Flask(__name__)

    # Load configuration
    if config_class is None:
        env = os.getenv('FLASK_ENV', 'development')
        if env == 'production':
            config_class = ProductionConfig
        else:
            config_class = DevelopmentConfig
    app.config.from_object(config_class)

    # Add logging
#    logger = logging.getLogger(__name__)
#    logging.basicConfig(level=logging.INFO)
#    app.logger.info(f"Using configuration: {config_class.__name__}")
#    app.logger.info(f"SQLALCHEMY_DATABASE_URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

    # Configure logging
    if not app.debug:
        # Log to a file in production
        file_handler = RotatingFileHandler('ai_assistant.log', maxBytes=10240, backupCount=10)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
        file_handler.setFormatter(formatter)
        app.logger.addHandler(file_handler)
    else:
        # Log to console in development
        logging.basicConfig(level=logging.DEBUG)


    # Register blueprints **before** initializing extensions
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(email_handler_bp, url_prefix='/email')
    app.register_blueprint(webhooks_bp, url_prefix='/webhooks')

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)  # Initialize CSRF protection


    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'


    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.context_processor
    def inject_current_year():
        return {'current_year': datetime.utcnow().year}

    return app
