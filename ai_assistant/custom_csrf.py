from flask import request
from flask_wtf.csrf import CSRFProtect, validate_csrf
from flask_wtf._compat import FlaskWTFDeprecationWarning

class CustomCSRFProtect(CSRFProtect):
    def validate_csrf(self, data=None):
        if data is None:
            data = request.headers.get('X-CSRFToken')  # Get token from header
        if not data:
            data = request.form.get('csrf_token')  # Fallback to form data
        return super().validate_csrf(data)

csrf = CustomCSRFProtect()