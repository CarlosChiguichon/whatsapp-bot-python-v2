import logging
import json
import re
import os
import requests
import time
from urllib.parse import urljoin
from flask import current_app, jsonify
from app.services.ai_service import generate_assistant_response
from app.utils.session_manager import SessionManager

# Inicializar el logger
logger = logging.getLogger(__name__)

# Almacenar estos valores globalmente para que estén disponibles fuera del contexto de la aplicación
whatsapp_config = {
    'access_token': None,
    'version': None,
    'phone_number_id': None
}

def init_whatsapp_config(app):
    """
    Inicializa la configuración de WhatsApp para uso fuera del contexto de la aplicación.
    Esta función debe llamarse durante el inicio de la aplicación.
    """
    with app.app_context():
        whatsapp_config['access_token'] = app.config['ACCESS_TOKEN']
        whatsapp_config['version'] = app.config['VERSION']
        whatsapp_config['phone_number_id'] = app.config['PHONE_NUMBER_ID']
        
        # Inicializar SessionManager con configuración de la aplicación
        session_timeout = app.config.get('SESSION_TIMEOUT', 600)
        warning_time = app.config.get('SESSION_WARNING_TIME', 300)
        session_manager = SessionManager.get_instance(
            session_timeout=session_timeout,
            inactivity_warning=warning_time
        )
        
        # Configurar función de envío de mensajes
        session_manager.set_send_message_function(send_whatsapp_message_background)
        
        # Cargar sesiones si existe el archivo
        sessions_file = app.config.get('SESSIONS_FILE_PATH', 'sessions.json')
        if os.path.exists(sessions_file):
            session_manager.load_sessions(sessions_file)
        
        logger.info("WhatsApp configuration initialized")

def get_text_message_input(recipient, text):
    """
    Crea la estructura JSON para enviar un mensaje de texto a WhatsApp.
    
    Args:
        recipient (str): Número de teléfono del destinatario
        text (str): Texto del mensaje
        
    Returns:
        str: JSON serializado con el mensaje
    """
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }
    )

def get_session_manager():
    """
    Obtiene la instancia única del SessionManager.
    
    Returns:
        SessionManager: Instancia del gestor de sesiones
    """
    return SessionManager.get_instance()

def log_http_response(response):
    """
    Registra la respuesta HTTP en el log.
    
    Args:
        response: Objeto de respuesta HTTP
    """
    logger.info(f"Status: {response.status_code}")
    logger.info(f"Content-type: {response.headers.get('content-type')}")
    logger.info(f"Body: {response.text}")

def send_message(data):
    """
    Envía un mensaje a la API de WhatsApp.
    Utiliza el contexto de aplicación Flask.
    
    Args:
        data (str): Datos del mensaje en formato JSON
        
    Returns:
        Response: Objeto de respuesta HTTP
    """
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}",
    }
    url = f"https://graph.facebook.com/{current_app.config['VERSION']}/{current_app.config['PHONE_NUMBER_ID']}/messages"
    
    try:
        response = requests.post(
            url, data=data, headers=headers, timeout=10
        )
        response.raise_for_status()  # Lanza excepción si el código de estado es 4xx o 5xx
    except requests.Timeout:
        logger.error("Timeout occurred while sending message")
        return jsonify({"status": "error", "message": "Request timed out"}), 408
    except requests.RequestException as e:
        logger.error(f"Request failed due to: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to send message"}), 500
    except Exception as e:
        logger.error(f"Unexpected error sending message: {str(e)}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500
    else:
        log_http_response(response)
        return response

def send_whatsapp_message_background(recipient, text):
    """
    Función para enviar mensajes de WhatsApp desde hilos en segundo plano.
    Utiliza la configuración almacenada globalmente en lugar de current_app.
    
    Args:
        recipient (str): Número de teléfono del destinatario
        text (str): Texto del mensaje
        
    Returns:
        Response: Objeto de respuesta HTTP o None en caso de error
    """
    message_data = get_text_message_input(recipient, text)
    
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {whatsapp_config['access_token']}",
    }
    
    url = f"https://graph.facebook.com/{whatsapp_config['version']}/{whatsapp_config['phone_number_id']}/messages"
    
    try:
        # Implementación de reintento con retroceso exponencial
        max_retries = 3
        retry_delay = 1  # Segundos
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    url, data=message_data, headers=headers, timeout=10
                )
                response.raise_for_status()
                logger.info(f"Mensaje enviado a {recipient}")
                return response
            except (requests.RequestException, requests.Timeout) as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Error al enviar mensaje, reintentando ({attempt+1}/{max_retries}): {str(e)}")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Retroceso exponencial
                else:
                    raise
        
    except Exception as e:
        logger.error(f"Error al enviar mensaje a {recipient}: {str(e)}")
        return None

def process_text_for_whatsapp(text):
    """
    Procesa el texto para formateo correcto en WhatsApp.
    
    Args:
        text (str): Texto a procesar
        
    Returns:
        str: Texto formateado para WhatsApp
    """
    if not text:
        return ""
        
    # Eliminar corchetes
    pattern = r"\【.*?\】"
    text = re.sub(pattern, "", text).strip()
    
    # Convertir formato markdown a WhatsApp
    pattern = r"\*\*(.*?)\*\*"
    replacement = r"*\1*"
    text = re.sub(pattern, replacement, text)
    
    # Convertir enlaces
    pattern = r"\[(.*?)\]\((.*?)\)"
    replacement = r"\1: \2"
    text = re.sub(pattern, replacement, text)
    
    # Eliminar caracteres no imprimibles
    text = re.sub(r'[\x00-\x1F\x7F]', '', text)
    
    return text

def detect_ticket_intent(message):
    """
    Detecta si el usuario tiene la intención de crear un ticket de soporte.
    
    Args:
        message (str): Mensaje del usuario
        
    Returns:
        bool: True si se detecta intención de crear ticket, False en caso contrario
    """
    # Palabras clave que podrían indicar la intención de crear un ticket
    ticket_keywords = [
        "problema", "error", "falla", "ticket", "ayuda", "soporte", "no funciona",
        "issue", "bug", "help", "support", "not working", "broken", "doesn't work"
    ]
    
    message_lower = message.lower()
    
    # Buscar coincidencias con palabras clave
    for keyword in ticket_keywords:
        if keyword in message_lower:
            return True
    
    return False

def process_whatsapp_message(body):
    """
    Procesa un mensaje entrante de WhatsApp.
    
    Args:
        body (dict): Cuerpo del webhook de WhatsApp
    """
    try:
        # Extraer información del usuario
        wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
        name = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]
        message = body["entry"][0]["changes"][0]["value"]["messages"][0]
        
        if message.get("type") != "text":
            logger.info(f"Received non-text message from {wa_id}")
            send_whatsapp_message_background(
                wa_id, 
                "Lo siento, actualmente solo puedo procesar mensajes de texto."
            )
            return
            
        message_body = message["text"]["body"]
        
        # Obtener gestor de sesiones
        session_manager = get_session_manager()
        
        # Obtener o crear sesión para este usuario
        session = session_manager.get_session(wa_id)
        
        # Agregar mensaje al historial
        session_manager.add_message_to_history(wa_id, 'user', message_body)
        
        # Detectar comandos especiales
        if message_body.lower() in ["/restart", "/reiniciar"]:
            session_manager.restart_session(wa_id)
            response = "He reiniciado nuestra conversación. ¿En qué puedo ayudarte?"
            session_manager.add_message_to_history(wa_id, 'assistant', response)
            send_whatsapp_message_background(wa_id, response)
            return
            
        # Procesar basado en el estado de la sesión
        if session['state'] == 'INITIAL' and message_body.lower() in ['hola', 'hi', 'hello']:
            # Mensaje de bienvenida para nuevos usuarios
            response = f"¡Hola {name}! Bienvenido. ¿En qué puedo ayudarte hoy?"
            session_manager.update_session(wa_id, state='AWAITING_QUERY')
        
        elif session['state'] == 'TICKET_CREATION':
            # Si estamos en proceso de crear un ticket, continuar ese flujo
            if 'ticket_subject' not in session['context']:
                session['context']['ticket_subject'] = message_body
                response = "Gracias. Por favor describe el problema en detalle."
                session_manager.update_session(wa_id, context=session['context'])
            else:
                # Completar la creación del ticket con la información recopilada
                subject = session['context']['ticket_subject']
                description = message_body
                
                # Aquí irías la lógica para crear el ticket
                # from app.services.odoo_integration import create_odoo_ticket
                # ticket_result = create_odoo_ticket(name, wa_id, "", subject, description)
                logger.info(f"Would create ticket: {subject} for {name}")
                
                response = "¡Gracias! Tu ticket ha sido creado. Un agente de soporte te contactará pronto."
                # Reiniciar el estado para nuevas consultas
                session_manager.update_session(wa_id, state='AWAITING_QUERY', context={})
        
        # Verificar si el mensaje indica intención de crear un ticket
        elif detect_ticket_intent(message_body) and session['state'] != 'TICKET_CREATION':
            response = "Parece que necesitas ayuda con un problema. ¿Podrías proporcionar un breve título o asunto para tu ticket de soporte?"
            session_manager.update_session(wa_id, state='TICKET_CREATION', context={})
        
        else:
            # Para cualquier otro estado o mensaje, procesar con OpenAI
            # Usar thread_id si está disponible para mantener conversación
            thread_id = session.get('thread_id')
            
            # Llamar a OpenAI con contexto preservado
            response = generate_response(message_body, wa_id, name)
        
        # Procesar respuesta para formato de WhatsApp
        response = process_text_for_whatsapp(response)
        
        # Agregar respuesta al historial
        session_manager.add_message_to_history(wa_id, 'assistant', response)
        
        # Enviar respuesta a WhatsApp
        send_whatsapp_message_background(wa_id, response)
        
        # Guardar periódicamente las sesiones
        if session_manager.sessions:
            try:
                session_manager.save_sessions('sessions.json')
            except Exception as e:
                logger.error(f"Error saving sessions: {str(e)}")
        
    except KeyError as e:
        logger.error(f"Missing key in webhook payload: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing WhatsApp message: {str(e)}")

def is_valid_whatsapp_message(body):
    """
    Verifica si el webhook entrante tiene una estructura válida de mensaje de WhatsApp.
    
    Args:
        body (dict): Cuerpo del webhook
        
    Returns:
        bool: True si es un mensaje válido, False en caso contrario
    """
    try:
        return (
            body.get("object") == "whatsapp_business_account" and
            body.get("entry") and
            body["entry"][0].get("changes") and
            body["entry"][0]["changes"][0].get("value") and
            body["entry"][0]["changes"][0]["value"].get("messages") and
            body["entry"][0]["changes"][0]["value"]["messages"][0]
        )
    except (KeyError, IndexError, TypeError):
        return False