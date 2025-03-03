import hashlib
import hmac
import os
import base64
import time
from flask import request
from app.utils.logger import get_logger

logger = get_logger(__name__)

def verify_whatsapp_signature(request):
    """
    Verifica la firma de las solicitudes entrantes de WhatsApp.
    
    Args:
        request: Objeto de solicitud Flask
        
    Returns:
        bool: True si la firma es válida, False en caso contrario
    """
    # El token de App Secret debe estar en las variables de entorno
    app_secret = os.getenv("WHATSAPP_APP_SECRET")
    
    if not app_secret:
        logger.warning("No se ha configurado WHATSAPP_APP_SECRET")
        return True  # Permitir en desarrollo si no hay secreto configurado
    
    # Obtener la firma y timestamp de los headers
    signature = request.headers.get("X-Hub-Signature-256", "")
    
    if not signature:
        logger.warning("Solicitud sin firma X-Hub-Signature-256")
        return False
    
    # Validar el formato de la firma
    if not signature.startswith("sha256="):
        logger.warning("Formato de firma inválido")
        return False
    
    # Extraer el valor del hash
    received_hash = signature.split("sha256=")[1]
    
    # Calcular el hash esperado
    body = request.get_data()
    expected_hash = hmac.new(
        app_secret.encode(),
        msg=body,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    # Comparar hashes (usando comparación de tiempo constante)
    return hmac.compare_digest(received_hash, expected_hash)

def rate_limit_check(ip_address, limit=100, window=3600):
    """
    Implementación simple de rate limiting basada en IP.
    En producción, usar Redis u otra solución de caché distribuida.
    
    Args:
        ip_address (str): Dirección IP para verificar
        limit (int): Número máximo de solicitudes en la ventana de tiempo
        window (int): Ventana de tiempo en segundos
        
    Returns:
        bool: True si está dentro del límite, False si excede
    """
    # Nota: Esta es una implementación en memoria simple
    # En producción, deberías usar Redis u otra solución de caché distribuida
    
    # Simula un almacenamiento temporal (usar un diccionario real en la clase)
    if not hasattr(rate_limit_check, "store"):
        rate_limit_check.store = {}
    
    current_time = int(time.time())
    
    # Limpiar registros antiguos
    for ip in list(rate_limit_check.store.keys()):
        if rate_limit_check.store[ip]["timestamp"] < current_time - window:
            del rate_limit_check.store[ip]
    
    # Verificar o inicializar el contador para esta IP
    if ip_address not in rate_limit_check.store:
        rate_limit_check.store[ip_address] = {
            "count": 1,
            "timestamp": current_time
        }
        return True
    
    # Actualizar y verificar el contador
    rate_limit_check.store[ip_address]["count"] += 1
    
    if rate_limit_check.store[ip_address]["count"] > limit:
        logger.warning(f"Rate limit excedido para IP: {ip_address}")
        return False
    
    return True

def sanitize_input(text):
    """
    Sanitiza el texto de entrada para prevenir inyecciones.
    
    Args:
        text (str): Texto a sanitizar
        
    Returns:
        str: Texto sanitizado
    """
    if not text:
        return ""
    
    # Eliminar caracteres potencialmente dañinos
    # Esta es una implementación básica, considerá usar una biblioteca 
    # especializada como bleach para casos más complejos
    
    # Reemplazar caracteres problemáticos
    replacements = {
        "<": "&lt;",
        ">": "&gt;",
        "&": "&amp;",
        '"': "&quot;",
        "'": "&#x27;",
        "/": "&#x2F;",
        "\\": "&#x5C;",
        "`": "&#x60;"
    }
    
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    
    return text

def is_valid_phone_number(phone_number):
    """
    Verifica si un número de teléfono tiene un formato válido.
    
    Args:
        phone_number (str): Número de teléfono a verificar
        
    Returns:
        bool: True si el formato es válido, False en caso contrario
    """
    if not phone_number:
        return False
    
    # Eliminar espacios, guiones y paréntesis
    clean_number = ''.join(c for c in phone_number if c.isdigit())
    
    # Verificar longitud (entre 10 y 15 dígitos para números internacionales)
    return 10 <= len(clean_number) <= 15