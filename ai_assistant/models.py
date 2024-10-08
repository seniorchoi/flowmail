# ai_assistant/models.py
from .extensions import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'users'  # Optional: explicitly name your table
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(128), nullable=False, default='Default Name')
    password = db.Column(db.String(512), nullable=False)
    role = db.Column(db.String(128), nullable=True)  # Job Title
    
    # New preference fields
    assistant_personality = db.Column(db.String(256), nullable=True)  # Comma-separated personality traits
    about_me = db.Column(db.Text, nullable=True)  # Comma-separated about me details

    #strip info
    stripe_customer_id = db.Column(db.String(100), nullable=True)
    is_premium = db.Column(db.Boolean, default=False)
    subscription_status = db.Column(db.String(50), nullable=True)
    
    


    def __repr__(self):
        return f'<User {self.email}>'
