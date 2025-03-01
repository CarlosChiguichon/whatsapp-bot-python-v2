from flask import Flask
from app.config import load_configurations, configure_logging
from app.utils.whatsapp_utils import init_whatsapp_config

def create_app():
    app = Flask(__name__)
    
    # Load configurations and logging settings
    load_configurations(app)
    configure_logging()
    
    # Initialize WhatsApp config for background threads
    with app.app_context():
        init_whatsapp_config(app)
    
    # Import and register blueprints
    from .views import webhook_blueprint
    app.register_blueprint(webhook_blueprint)
    
    return app