import time
import threading
import json
import logging
from datetime import datetime, timedelta

# Inicializar el logger
logger = logging.getLogger(__name__)

class SessionManager:
    """
    Gestor de sesiones para el chatbot de WhatsApp.
    Mantiene el estado de las conversaciones con los usuarios y maneja la expiración de sesiones.
    """
    
    _instance = None
    
    @classmethod
    def get_instance(cls, session_timeout=None, inactivity_warning=None):
        """
        Implementación de Singleton para asegurar una única instancia.
        
        Args:
            session_timeout (int, optional): Tiempo en segundos antes de que una sesión expire
            inactivity_warning (int, optional): Tiempo en segundos antes de enviar advertencia
            
        Returns:
            SessionManager: Instancia única del SessionManager
        """
        if cls._instance is None:
            cls._instance = cls(session_timeout, inactivity_warning)
        return cls._instance
    
    def __init__(self, session_timeout=600, inactivity_warning=300):
        """
        Inicializa el gestor de sesiones.
        
        Args:
            session_timeout (int): Tiempo en segundos antes de que una sesión expire por inactividad
            inactivity_warning (int): Tiempo en segundos antes de enviar advertencia
        """
        self.sessions = {}
        self.session_timeout = session_timeout
        self.inactivity_warning = inactivity_warning
        self.lock = threading.RLock()  # Para operaciones thread-safe
        
        # Función para enviar mensajes
        self.send_message_func = None
        
        # Iniciar thread de limpieza en segundo plano
        self.cleanup_thread = threading.Thread(target=self._cleanup_expired_sessions, daemon=True)
        self.cleanup_thread.start()
        
        logger.info(f"SessionManager initialized with timeout={session_timeout}s, warning={inactivity_warning}s")
    
    def set_send_message_function(self, func):
        """
        Establece la función para enviar mensajes a WhatsApp.
        
        Args:
            func: Función que acepta user_id y message como parámetros
        """
        self.send_message_func = func
        logger.info("Message sending function set")
    
    def get_session(self, user_id):
        """
        Obtiene la sesión de un usuario. Si no existe, crea una nueva.
        
        Args:
            user_id (str): ID de WhatsApp del usuario
            
        Returns:
            dict: Objeto de sesión del usuario
        """
        with self.lock:
            if user_id not in self.sessions:
                # Crear nueva sesión
                self.sessions[user_id] = {
                    'created_at': datetime.now(),
                    'last_activity': datetime.now(),
                    'state': 'INITIAL',
                    'context': {},
                    'thread_id': None,  # Para OpenAI Assistants API
                    'message_history': [],
                    'inactivity_warning_sent': False,
                    'closing_notice_sent': False,
                    'meta': {
                        'total_messages': 0,
                        'session_restarts': 0
                    }
                }
                logger.info(f"Created new session for user