from flask import Blueprint

email_handler = Blueprint('email_handler', __name__)

from . import routes  # Import routes to register them with the blueprint
