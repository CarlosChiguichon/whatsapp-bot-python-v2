import os
import logging
import time
import json
from openai import OpenAI

# Configurar logger
logger = logging.getLogger(__name__)

# Crear una única instancia global del cliente OpenAI
_openai_client = None

def get_openai_client():
    """
    Obtiene o crea una instancia global del cliente OpenAI.
    Maneja compatibilidad con diferentes versiones de la API.
    
    Returns:
        OpenAI: Cliente OpenAI
    """
    global _openai_client
    
    if _openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        
        try:
            # Intento 1: Constructor básico (versiones más nuevas)
            _openai_client = OpenAI(api_key=api_key)
            logger.info("OpenAI client initialized (basic constructor)")
        except Exception as e1:
            logger.warning(f"Basic OpenAI initialization failed: {str(e1)}")
            
            try:
                # Intento 2: Configuración directa (compatibilidad hacia atrás)
                import openai
                openai.api_key = api_key
                _openai_client = openai.Client()
                logger.info("OpenAI client initialized (legacy method)")
            except Exception as e2:
                logger.error(f"Failed to initialize OpenAI client: {str(e2)}")
                raise RuntimeError("Could not initialize OpenAI client") from e2
    
    return _openai_client

def generate_response(message, user_id, user_name=None):
    """
    Genera una respuesta utilizando el asistente de OpenAI.
    
    Args:
        message (str): Mensaje del usuario
        user_id (str): ID del usuario de WhatsApp
        user_name (str, optional): Nombre del usuario
        
    Returns:
        str: Texto de respuesta generada
    """
    try:
        # Obtener cliente OpenAI
        client = get_openai_client()
        
        # Buscar thread existente para este usuario en el archivo de estados
        thread_id = None
        try:
            with open('threads.json', 'r') as f:
                threads = json.load(f)
                thread_id = threads.get(user_id)
        except (FileNotFoundError, json.JSONDecodeError):
            threads = {}
        
        # Si no hay thread, crear uno nuevo
        if not thread_id:
            logger.info(f"Creating new thread for {user_name} with wa_id {user_id}")
            thread = client.beta.threads.create()
            thread_id = thread.id
            
            # Guardar thread_id
            threads[user_id] = thread_id
            with open('threads.json', 'w') as f:
                json.dump(threads, f)
        
        # Obtener ID del asistente
        assistant_id = os.getenv("ASSISTANT_ID")
        if not assistant_id:
            logger.error("ASSISTANT_ID not found in environment variables")
            return "Error: No se ha configurado un asistente. Por favor contacta al administrador."
        
        # Añadir contexto del usuario si está disponible
        user_context = f"The user's name is {user_name}. " if user_name else ""
        full_message = user_context + message
        
        # Agregar mensaje del usuario al thread
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=full_message
        )
        
        # Ejecutar el asistente
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )
        
        # Esperar a que termine la ejecución
        max_wait_time = 60  # segundos
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            
            if run_status.status == "completed":
                # Obtener mensajes del thread
                messages = client.beta.threads.messages.list(
                    thread_id=thread_id
                )
                
                # Obtener la respuesta del asistente (primer mensaje)
                for msg in messages.data:
                    if msg.role == "assistant":
                        for content_block in msg.content:
                            if content_block.type == "text":
                                return content_block.text.value
                
                # Si no encontramos respuesta de texto
                logger.warning("No text content found in assistant response")
                return "No se pudo obtener una respuesta. Por favor, intenta de nuevo."
            
            elif run_status.status in ["failed", "cancelled", "expired"]:
                logger.error(f"Run failed with status {run_status.status}")
                return "Lo siento, hubo un problema procesando tu mensaje. Por favor, intenta de nuevo más tarde."
            
            # Esperar antes de verificar de nuevo
            time.sleep(1)
        
        # Si excedimos el tiempo de espera
        logger.error("Run timed out")
        return "Lo siento, la respuesta está tomando demasiado tiempo. Por favor, intenta de nuevo más tarde."
        
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        return "Lo siento, ha ocurrido un error inesperado. Por favor, inténtalo de nuevo más tarde."