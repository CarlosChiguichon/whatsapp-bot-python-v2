import os
import logging
import time
import json
import importlib

# Configurar logger
logger = logging.getLogger(__name__)

def monkey_patch_openai():
    """
    Modifica la clase Client de OpenAI para ignorar el parámetro proxies.
    """
    try:
        import openai
        original_init = openai.OpenAI.__init__
        
        def patched_init(self, *args, **kwargs):
            # Eliminar el parámetro proxies si existe
            if 'proxies' in kwargs:
                logger.warning("Removing 'proxies' parameter from OpenAI client initialization")
                del kwargs['proxies']
            return original_init(self, *args, **kwargs)
        
        # Aplicar el parche
        openai.OpenAI.__init__ = patched_init
        logger.info("OpenAI client patched to ignore proxies parameter")
    except Exception as e:
        logger.error(f"Failed to patch OpenAI client: {str(e)}")

# Aplicar el parche inmediatamente al importar este módulo
monkey_patch_openai()

def create_openai_client():
    """
    Crea un cliente OpenAI con manejo de errores.
    """
    try:
        import openai
        api_key = os.getenv("OPENAI_API_KEY")
        
        # Crear cliente sin proxies
        client = openai.OpenAI(api_key=api_key)
        return client
    except Exception as e:
        logger.error(f"Error creating OpenAI client: {str(e)}")
        raise

def chat_completion(message):
    """
    Función simple para probar si el cliente OpenAI funciona.
    """
    try:
        client = create_openai_client()
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": message}
            ]
        )
        
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error in chat completion: {str(e)}")
        return f"Error: {str(e)}"

def get_or_create_thread(user_id):
    """
    Obtiene un thread existente o crea uno nuevo.
    """
    try:
        client = create_openai_client()
        
        # Intentar cargar threads existentes
        thread_id = None
        try:
            if os.path.exists('threads.json'):
                with open('threads.json', 'r') as f:
                    threads = json.load(f)
                    thread_id = threads.get(user_id)
        except Exception:
            threads = {}
        
        # Si no hay thread para este usuario, crear uno
        if not thread_id:
            thread = client.beta.threads.create()
            thread_id = thread.id
            
            # Guardar el nuevo thread
            threads[user_id] = thread_id
            with open('threads.json', 'w') as f:
                json.dump(threads, f)
            
            logger.info(f"Created new thread {thread_id} for user {user_id}")
        
        return thread_id
    except Exception as e:
        logger.error(f"Error in get_or_create_thread: {str(e)}")
        raise

def generate_assistant_response(message, user_id, user_name=None):
    """
    Genera una respuesta usando el asistente de OpenAI.
    """
    try:
        client = create_openai_client()
        assistant_id = os.getenv("ASSISTANT_ID")
        
        if not assistant_id:
            return "Error: No se ha configurado un asistente. Contacta al administrador."
        
        # Obtener o crear thread
        thread_id = get_or_create_thread(user_id)
        
        # Crear mensaje con contexto
        user_context = f"The user's name is {user_name}. " if user_name else ""
        full_message = user_context + message
        
        # Añadir mensaje al thread
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
        
        # Esperar a que termine
        max_wait_time = 60  # segundos
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            
            if run_status.status == "completed":
                # Obtener respuesta
                messages = client.beta.threads.messages.list(thread_id=thread_id)
                
                for msg in messages.data:
                    if msg.role == "assistant":
                        for content in msg.content:
                            if content.type == "text":
                                return content.text.value
                
                return "No se encontró una respuesta de texto."
                
            elif run_status.status in ["failed", "cancelled", "expired"]:
                logger.error(f"Run failed with status: {run_status.status}")
                return "Lo siento, hubo un problema al procesar tu mensaje."
                
            # Esperar antes de verificar de nuevo
            time.sleep(1)
        
        # Si se acabó el tiempo
        logger.error("Run timed out")
        return "Lo siento, la respuesta está tomando demasiado tiempo."
        
    except Exception as e:
        logger.error(f"Error generating assistant response: {str(e)}")
        return "Lo siento, ha ocurrido un error inesperado. Por favor, inténtalo de nuevo más tarde."