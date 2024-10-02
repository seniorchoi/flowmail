# ai_assistant/config.py
import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev_secret_key')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAILGUN_API_KEY = os.getenv('MAILGUN_API_KEY')
    MAILGUN_WEBHOOK_SIGNING_KEY = os.getenv('MAILGUN_WEBHOOK_SIGNING_KEY')
    MAILGUN_DOMAIN = os.getenv('MAILGUN_DOMAIN')
    MAILGUN_BASE_URL = os.getenv('MAILGUN_BASE_URL')
    FROM_EMAIL = os.getenv('FROM_EMAIL')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')

    SESSION_COOKIE_SECURE = True  # Ensures cookies are sent over HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'  # Adjust as needed

class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'database.db')
    DEBUG = True

class ProductionConfig(Config):
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("No DATABASE_URL environment variable set for production")
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = database_url
    DEBUG = False
