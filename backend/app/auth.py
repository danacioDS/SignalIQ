import os
from functools import wraps
from flask import request, jsonify

# API Key para autenticación
API_KEY = os.environ.get('API_KEY', 'signaliq-secret-key-2026')

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != API_KEY:
            return jsonify({'error': 'Unauthorized: Invalid API Key'}), 401
        return f(*args, **kwargs)
    return decorated

def require_api_key_optional(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key and api_key != API_KEY:
            return jsonify({'error': 'Unauthorized: Invalid API Key'}), 401
        return f(*args, **kwargs)
    return decorated
