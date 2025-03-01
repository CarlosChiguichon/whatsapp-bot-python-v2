import os
import logging
from app import create_app

# Crear la aplicación Flask
app = create_app()

if __name__ == "__main__":
    # Configurar puerto (por defecto 8000 o el definido en variable de entorno)
    port = int(os.environ.get("PORT", 8000))
    
    # Determinar si usar modo debug
    debug = os.environ.get("FLASK_ENV") == "development"
    
    logging.info(f"Starting WhatsApp Bot on port {port}, debug mode: {debug}")
    
    # Iniciar servidor
    app.run(host="0.0.0.0", port=port, debug=debug)