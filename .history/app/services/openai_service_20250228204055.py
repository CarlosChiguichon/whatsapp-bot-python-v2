import os
import logging
import time
from openai import OpenAI
from flask import current_app

# Inicializar el logger
logger = logging.getLogger(__name__)

class OpenAIService:
    """
    Servicio para interactuar con la API de OpenAI.
    """
    
    def __init__(self, api_key=None, assistant_id=None):
        """
        Inicializa el servicio de OpenAI.
        
        Args:
            api_key (str, optional): API key de OpenAI. Si no se proporciona, se usa la configuración de la app.
            assistant_id (str, optional): ID del asistente. Si no se proporciona, se usa la configuración de la app.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.assistant_id = assistant_id or os.getenv("ASSISTANT_ID")
        
        # Inicializar cliente OpenAI sin el parámetro proxies
        self.client = OpenAI(api_key=self.api_key)
        
        # Cache de threads para usuarios
        self.thread_cache = {}
        
        logger.info("OpenAI service initialized")
    
    def get_or_create_thread(self, user_id):
        """
        Obtiene un thread existente o crea uno nuevo para un usuario.
        
        Args:
            user_id (str): ID del usuario
            
        Returns:
            str: ID del thread
        """
        if user_id in self.thread_cache:
            return self.thread_cache[user_id]
        
        try:
            # Crear un nuevo thread
            thread = self.client.beta.threads.create()
            thread_id = thread.id
            
            # Guardar en caché
            self.thread_cache[user_id] = thread_id
            logger.info(f"Created new thread {thread_id} for user {user_id}")
            
            return thread_id
        except Exception as e:
            logger.error(f"Error creating thread: {str(e)}")
            raise
    
    def wait_for_run_completion(self, thread_id, run_id, max_wait_time=60, check_interval=1):
        """
        Espera a que se complete una ejecución.
        
        Args:
            thread_id (str): ID del thread
            run_id (str): ID de la ejecución
            max_wait_time (int): Tiempo máximo de espera en segundos
            check_interval (int): Intervalo entre comprobaciones en segundos
            
        Returns:
            obj: Objeto de ejecución completada
        """
        start_time = time.time()
        while time.time() - start_time < max_wait_time:
            try:
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run_id
                )
                
                if run.status in ["completed", "failed", "cancelled", "expired"]:
                    logger.info(f"Run {run_id} completed with status: {run.status}")
                    return run
                
                # Esperar antes de la siguiente verificación
                time.sleep(check_interval)
            except Exception as e:
                logger.error(f"Error checking run status: {str(e)}")
                # Continuar esperando en caso de error temporal
                time.sleep(check_interval)
        
        # Si se excede el tiempo, cancelar la ejecución
        logger.warning(f"Run {run_id} exceeded max wait time, cancelling")
        self.client.beta.threads.runs.cancel(
            thread_id=thread_id,
            run_id=run_id
        )
        raise TimeoutError(f"Run {run_id} exceeded max wait time of {max_wait_time} seconds")
    
    def generate_response(self, message, user_id, user_name=None, max_retries=2):
        """
        Genera una respuesta a partir del mensaje de un usuario.
        
        Args:
            message (str): Mensaje del usuario
            user_id (str): ID del usuario
            user_name (str, optional): Nombre del usuario
            max_retries (int): Número máximo de reintentos en caso de error
            
        Returns:
            str: Texto de respuesta generada
        """
        # Obtener o crear thread para este usuario
        try:
            thread_id = self.get_or_create_thread(user_id)
            
            # Añadir contexto del usuario si está disponible
            context = f"The user's name is {user_name}. " if user_name else ""
            user_message = context + message
            
            # Añadir mensaje al thread
            self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=user_message
            )
            
            # Ejecutar el assistant
            run = self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=self.assistant_id
            )
            
            # Esperar a que termine la ejecución
            run = self.wait_for_run_completion(thread_id, run.id)
            
            # Si la ejecución falló, reintentar
            retry_count = 0
            while run.status != "completed" and retry_count < max_retries:
                logger.warning(f"Run failed with status {run.status}, retrying ({retry_count+1}/{max_retries})")
                
                # Pequeño retraso antes de reintentar
                time.sleep(1)
                
                # Crear una nueva ejecución
                run = self.client.beta.threads.runs.create(
                    thread_id=thread_id,
                    assistant_id=self.assistant_id
                )
                
                # Esperar a que termine
                run = self.wait_for_run_completion(thread_id, run.id)
                retry_count += 1
            
            # Si después de los reintentos sigue fallando
            if run.status != "completed":
                logger.error(f"Failed to generate response after {max_retries} retries")
                return "Lo siento, estoy teniendo problemas para generar una respuesta. Por favor, inténtalo más tarde."
            
            # Obtener el último mensaje (respuesta del assistant)
            messages = self.client.beta.threads.messages.list(thread_id=thread_id)
            
            # El más reciente primero
            for message in messages.data:
                if message.role == "assistant":
                    # Extraer el contenido de texto
                    for content in message.content:
                        if content.type == "text":
                            return content.text.value
            
            # Si no se encontró contenido de texto
            logger.warning("No text content found in assistant response")
            return "Lo siento, no pude generar una respuesta coherente. Por favor, intenta reformular tu pregunta."
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "Lo siento, ocurrió un error al procesar tu mensaje. Por favor, inténtalo de nuevo."

# Función para generar respuestas (mantiene compatibilidad con código existente)
def generate_response(message, user_id, user_name=None):
    """
    Genera una respuesta utilizando el servicio de OpenAI.
    Esta función mantiene la interfaz original para compatibilidad.
    """
    try:
        # Obtener API key y assistant ID
        api_key = os.getenv("OPENAI_API_KEY")
        assistant_id = os.getenv("ASSISTANT_ID")
        
        # Crear servicio
        service = OpenAIService(api_key=api_key, assistant_id=assistant_id)
        
        # Generar respuesta
        return service.generate_response(message, user_id, user_name)
    except Exception as e:
        logger.error(f"Error in generate_response: {str(e)}")
        return "Lo siento, ha ocurrido un error inesperado. Por favor, inténtalo de nuevo más tarde."