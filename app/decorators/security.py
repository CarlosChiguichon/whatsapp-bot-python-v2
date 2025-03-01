from functools import wraps
from flask import current_app, jsonify, request
import logging
import hashlib
import hmac

def validate_signature(payload, signature):
    """
    Validate the incoming payload's signature against our expected signature
    """
    # Use the App Secret to hash the payload
    expected_signature = hmac.new(
        bytes(current_app.config["APP_SECRET"], "latin-1"),
        msg=payload.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()
    # Check if the signature matches
    return hmac.compare_digest(expected_signature, signature)

def signature_required(f):
    """
    Decorator to ensure that the incoming requests to our webhook are valid and signed with the correct signature.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        signature = request.headers.get("X-Hub-Signature-256", "")[
            7:
        ]  # Removing 'sha256='
        
        # Si no hay firma y estamos en modo desarrollo, permitimos la solicitud
        if not signature and current_app.config.get("FLASK_ENV") == "development":
            logging.warning("No signature provided, but allowing request in development mode")
            return f(*args, **kwargs)
            
        if not validate_signature(request.data.decode("utf-8"), signature):
            logging.warning("Signature verification failed!")
            return jsonify({"status": "error", "message": "Invalid signature"}), 403
            
        return f(*args, **kwargs)
    return decorated_function