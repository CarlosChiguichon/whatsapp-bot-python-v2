import requests
import os
from app.utils.logger import get_logger

logger = get_logger(__name__)

class WhatsAppClient:
    def __init__(self):
        self.token = os.getenv("WHATSAPP_TOKEN")
        self.phone_number_id = os.getenv("PHONE_NUMBER_ID")
        self.api_url = f"https://graph.facebook.com/v17.0/{self.phone_number_id}/messages"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def send_message(self, to, message_text):
        """
        Envía un mensaje de texto a un número de WhatsApp.
        
        Args:
            to (str): Número de destino en formato internacional sin +
            message_text (str): Texto del mensaje a enviar
        
        Returns:
            dict: Respuesta de la API de WhatsApp
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {
                "body": message_text
            }
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            
            logger.info(f"Mensaje enviado a {to}")
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al enviar mensaje: {str(e)}")
            return {"error": str(e)}