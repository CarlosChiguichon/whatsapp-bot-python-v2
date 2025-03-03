from app.whatsapp.client import WhatsAppClient
from app.openai.client import OpenAIClient
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Instancias de los clientes
whatsapp_client = WhatsAppClient()
openai_client = OpenAIClient()

def process_incoming_message(from_number, message_text):
    """
    Procesa un mensaje entrante y envía una respuesta.
    
    Args:
        from_number (str): Número de teléfono del remitente
        message_text (str): Texto del mensaje recibido
    """
    logger.info(f"Procesando mensaje de {from_number}: {message_text}")
    
    try:
        # Obtener respuesta del asistente de OpenAI
        ai_response = openai_client.get_assistant_response(message_text)
        
        # Enviar respuesta por WhatsApp
        whatsapp_client.send_message(from_number, ai_response)
        
        logger.info(f"Respuesta enviada a {from_number}")
        
    except Exception as e:
        logger.error(f"Error al procesar mensaje: {str(e)}")
        
        # Enviar mensaje de error genérico
        error_message = "Lo siento, ocurrió un error al procesar tu mensaje. Por favor, intenta nuevamente más tarde."
        whatsapp_client.send_message(from_number, error_message)