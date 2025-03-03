#!/usr/bin/env python
"""
Punto de entrada principal para la aplicación WhatsApp Bot.
Este archivo facilita la ejecución de la aplicación y puede
ser usado directamente o por un servidor WSGI como Gunicorn.
"""

import os
from dotenv import load_dotenv
from app.main import create_app

# Cargar variables de entorno
load_dotenv()

# Obtener configuración del entorno
app_env = os.getenv("APP_ENV", "development")
port = int(os.getenv("PORT", 3000))
debug = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

# Crear aplicación
app = create_app(app_env)

if __name__ == "__main__":
    # Información de inicio
    print(f"Iniciando aplicación en modo: {app_env}")
    print(f"Servidor en: http://localhost:{port}")
    
    # Ejecutar servidor
    app.run(host="0.0.0.0", port=port, debug=debug)