import os
import openai
from app.utils.logger import get_logger

logger = get_logger(__name__)

class OpenAIClient:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.assistant_id = os.getenv("OPENAI_ASSISTANT_ID")
        openai.api_key = self.api_key
        
    def get_assistant_response(self, query):
        """
        Obtiene una respuesta del asistente de OpenAI.
        
        Args:
            query (str): La consulta del usuario
            
        Returns:
            str: Respuesta generada por el asistente
        """
        try:
            client = openai.OpenAI(api_key=self.api_key)
            
            # Crear un thread para la conversación
            thread = client.beta.threads.create()
            
            # Agregar el mensaje del usuario al thread
            client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=query
            )
            
            # Ejecutar el asistente en el thread
            run = client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=self.assistant_id
            )
            
            # Esperar a que termine la ejecución
            while run.status != "completed":
                run = client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
                
                if run.status == "failed":
                    logger.error(f"Error en la ejecución del asistente: {run.error}")
                    return "Lo siento, tuve un problema al procesar tu mensaje."
            
            # Obtener la respuesta
            messages = client.beta.threads.messages.list(
                thread_id=thread.id
            )
            
            # La respuesta más reciente del asistente estará al inicio de la lista
            for message in messages.data:
                if message.role == "assistant":
                    return message.content[0].text.value
            
            return "No pude generar una respuesta."
            
        except Exception as e:
            logger.error(f"Error al obtener respuesta de OpenAI: {str(e)}")
            return "Lo siento, ocurrió un error al procesar tu mensaje."