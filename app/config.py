import os
import logging
from dotenv import load_dotenv

# Cargar variables de entorno desde .env una sola vez al inicio
load_dotenv()

def load_configurations(app):
    """
    Carga las configuraciones de la aplicación desde variables de entorno.
    Centraliza toda la configuración para facilitar la gestión.
    """
    # Configuración de WhatsApp
    app.config["VERIFY_TOKEN"] = os.getenv("VERIFY_TOKEN")
    app.config["ACCESS_TOKEN"] = os.getenv("ACCESS_TOKEN")
    app.config["PHONE_NUMBER_ID"] = os.getenv("PHONE_NUMBER_ID")
    app.config["VERSION"] = os.getenv("VERSION", "v18.0")  # Valor por defecto
    
    # Configuración de OpenAI
    app.config["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
    app.config["ASSISTANT_ID"] = os.getenv("ASSISTANT_ID")
    
    # Configuración de Odoo
    app.config["ODOO_WEBHOOK_URL_TICKETS"] = os.getenv("ODOO_WEBHOOK_URL_TICKETS")
    
    # Configuración de sesiones
    app.config["SESSION_TIMEOUT"] = int(os.getenv("SESSION_TIMEOUT", "600"))  # 10 minutos por defecto
    app.config["SESSION_WARNING_TIME"] = int(os.getenv("SESSION_WARNING_TIME", "300"))  # 5 minutos por defecto
    app.config["SESSIONS_FILE_PATH"] = os.getenv("SESSIONS_FILE_PATH", "sessions.json")

def configure_logging():
    """
    Configura el sistema de logging para la aplicación.
    """
    log_level = os.getenv("LOG_LEVEL", "INFO")
    
    # Mapear el nombre del nivel de log a su constante en logging
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=level_map.get(log_level.upper(), logging.INFO),
        format=log_format
    )
    
    # Reducir verbosidad de logs de bibliotecas externas
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)