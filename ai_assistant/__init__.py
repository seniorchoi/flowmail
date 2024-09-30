# ai_assistant/__init__.py
import os
from flask import Flask
from .extensions import db, migrate, login_manager
from .config import DevelopmentConfig, ProductionConfig
from .auth.routes import auth_bp
from .main.routes import main_bp
from .email_handler.routes import email_handler
from .models import User
import logging

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
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)
    app.logger.info(f"Using configuration: {config_class.__name__}")
    app.logger.info(f"SQLALCHEMY_DATABASE_URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
   

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(email_handler, url_prefix='/email')

    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'


    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app
