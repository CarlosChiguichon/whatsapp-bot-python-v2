import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def test_openai_connection():
    """
    Prueba simple para verificar la conexión con OpenAI.
    """
    from app.services.ai_service import chat_completion
    
    print("Probando conexión con OpenAI...")
    result = chat_completion("Hola, ¿cómo estás?")
    print(f"Respuesta: {result}")
    print("Prueba completada.")

if __name__ == "__main__":
    test_openai_connection()