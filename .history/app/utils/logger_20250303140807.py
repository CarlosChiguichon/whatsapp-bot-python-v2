import logging
import os
import sys
from logging.handlers import RotatingFileHandler

# Configuración global
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DIR = "logs"

def setup_logger():
    """
    Configura el logger principal de la aplicación.
    
    Returns:
        logging.Logger: Logger configurado
    """
    # Crear directorio de logs si no existe
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    
    # Configurar logger raíz
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # Limpiar handlers existentes
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(console_handler)
    
    # Handler para archivo con rotación
    file_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, "whatsapp_bot.log"),
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(file_handler)
    
    return logger

def get_logger(name=None):
    """
    Obtiene un logger específico para un módulo.
    
    Args:
        name (str, optional): Nombre del módulo. Defaults a None.
        
    Returns:
        logging.Logger: Logger configurado
    """
    return logging.getLogger(name)