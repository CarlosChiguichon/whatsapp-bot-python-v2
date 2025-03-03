from flask import jsonify, request
import os
import json
from app.services.message_service import process_incoming_message
from app.utils.logger import get_logger
from app.utils.security import verify_whatsapp_signature, rate_limit_check, sanitize_input, is_valid_phone_number

logger = get_logger(__name__)

def verify_webhook(request):
    """
    Verifica el webhook cuando WhatsApp lo solicita.
    """
    verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN")
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == verify_token:
            logger.info("Webhook verificado exitosamente")
            return challenge, 200
        else:
            logger.warning("Falló la verificación del webhook")
            return "Forbidden", 403
    
    return "Bad Request", 400

def handle_webhook(request):
    """
    Maneja las notificaciones entrantes del webhook de WhatsApp.
    """
    try:
        # Verificar firma de WhatsApp para autenticidad
        if not verify_whatsapp_signature(request):
            logger.warning("Firma de WhatsApp inválida")
            return "Unauthorized", 401
        
        # Control de rate limiting basado en IP
        client_ip = request.remote_addr
        if not rate_limit_check(client_ip):
            logger.warning(f"Rate limit excedido para IP: {client_ip}")
            return "Too Many Requests", 429
        
        data = request.json
        logger.debug(f"Webhook recibido: {json.dumps(data)}")
        
        # Verificar si es un mensaje entrante y procesarlo
        if (data.get("object")
            and data.get("entry")
            and data["entry"][0].get("changes")
            and data["entry"][0]["changes"][0].get("value")
            and data["entry"][0]["changes"][0]["value"].get("messages")
            and data["entry"][0]["changes"][0]["value"]["messages"][0]):
            
            # Extraer información del mensaje
            phone_number_id = data["entry"][0]["changes"][0]["value"]["metadata"]["phone_number_id"]
            from_number = data["entry"][0]["changes"][0]["value"]["messages"][0]["from"]
            
            # Validar número de teléfono
            if not is_valid_phone_number(from_number):
                logger.warning(f"Número de teléfono inválido: {from_number}")
                return "OK", 200  # Devolver OK para no revelar validación
            
            # Obtener y sanitizar el texto del mensaje
            message_body = data["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"]
            sanitized_message = sanitize_input(message_body)
            
            # Procesar mensaje y enviar respuesta
            process_incoming_message(from_number, sanitized_message)
            
            return "OK", 200
        else:
            # Si no es un mensaje relevante, simplemente confirmar recepción
            return "OK", 200
    
    except Exception as e:
        logger.error(f"Error al procesar webhook: {str(e)}")
        return "Internal Server Error", 500