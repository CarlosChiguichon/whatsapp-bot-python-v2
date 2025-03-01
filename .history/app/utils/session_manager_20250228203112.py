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
                logger.info(f"Created new session for user {user_id}")
            else:
                # Actualizar timestamp de última actividad
                self.sessions[user_id]['last_activity'] = datetime.now()
                
                # Resetear los indicadores de advertencia cuando hay actividad
                self.sessions[user_id]['inactivity_warning_sent'] = False
                self.sessions[user_id]['closing_notice_sent'] = False
            
            return self.sessions[user_id]
    
    def update_session(self, user_id, **kwargs):
        """
        Actualiza propiedades específicas de la sesión de un usuario.
        
        Args:
            user_id (str): ID de WhatsApp del usuario
            **kwargs: Pares clave-valor para actualizar la sesión
        """
        with self.lock:
            if user_id in self.sessions:
                session = self.sessions[user_id]
                for key, value in kwargs.items():
                    if key in session:
                        session[key] = value
                
                # Actualizar timestamp de última actividad
                session['last_activity'] = datetime.now()
                
                # Resetear los indicadores de advertencia
                session['inactivity_warning_sent'] = False
                session['closing_notice_sent'] = False
                
                logger.debug(f"Updated session for user {user_id}: {kwargs.keys()}")
    
    def restart_session(self, user_id):
        """
        Reinicia la sesión de un usuario, conservando algunos metadatos.
        Útil cuando se quiere comenzar una nueva conversación pero mantener estadísticas.
        
        Args:
            user_id (str): ID de WhatsApp del usuario
        """
        with self.lock:
            if user_id in self.sessions:
                # Incrementar contador de reinicios
                session_restarts = self.sessions[user_id]['meta'].get('session_restarts', 0) + 1
                
                # Crear nueva sesión pero conservar meta
                self.sessions[user_id] = {
                    'created_at': datetime.now(),
                    'last_activity': datetime.now(),
                    'state': 'INITIAL',
                    'context': {},
                    'thread_id': None,
                    'message_history': [],
                    'inactivity_warning_sent': False,
                    'closing_notice_sent': False,
                    'meta': {
                        'total_messages': self.sessions[user_id]['meta'].get('total_messages', 0),
                        'session_restarts': session_restarts
                    }
                }
                logger.info(f"Restarted session for user {user_id} (restart #{session_restarts})")
    
    def end_session(self, user_id):
        """
        Finaliza la sesión de un usuario.
        
        Args:
            user_id (str): ID de WhatsApp del usuario
        """
        with self.lock:
            if user_id in self.sessions:
                del self.sessions[user_id]
                logger.info(f"Ended session for user {user_id}")
    
    def is_session_active(self, user_id):
        """
        Verifica si la sesión de un usuario está activa y no ha expirado.
        
        Args:
            user_id (str): ID de WhatsApp del usuario
            
        Returns:
            bool: True si la sesión está activa, False en caso contrario
        """
        with self.lock:
            if user_id not in self.sessions:
                return False
            
            session = self.sessions[user_id]
            expiration_time = session['last_activity'] + timedelta(seconds=self.session_timeout)
            return datetime.now() < expiration_time
    
    def _cleanup_expired_sessions(self):
        """
        Thread en segundo plano que limpia periódicamente las sesiones expiradas
        y envía notificaciones de inactividad.
        """
        while True:
            try:
                time.sleep(30)  # Verificar cada 30 segundos
                
                users_to_warn = []
                users_to_close = []
                
                # Recopilar usuarios que necesitan atención
                with self.lock:
                    current_time = datetime.now()
                    
                    for user_id, session in list(self.sessions.items()):
                        inactive_time = (current_time - session['last_activity']).total_seconds()
                        
                        # Usuarios para cerrar sesión
                        if inactive_time >= self.session_timeout and not session['closing_notice_sent']:
                            users_to_close.append(user_id)
                            session['closing_notice_sent'] = True