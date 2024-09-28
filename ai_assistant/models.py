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

    def __repr__(self):
        return f'<User {self.email}>'
