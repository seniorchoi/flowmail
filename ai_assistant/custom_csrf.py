from flask import request
from flask_wtf.csrf import CSRFProtect, validate_csrf
from flask_wtf._compat import FlaskWTFDeprecationWarning

class CustomCSRFProtect(CSRFProtect):
    def validate_csrf(self, data=None):
        if data is None:
            # Try to get the token from the headers
            data = request.headers.get('X-CSRFToken')
        if not data:
            # Try to get from form data as fallback
            data = request.form.get('csrf_token')
        validate_csrf(data)

csrf = CustomCSRFProtect()