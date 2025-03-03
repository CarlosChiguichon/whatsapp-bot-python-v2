from flask import Blueprint, request, jsonify
import os
from app.whatsapp.handlers import handle_webhook, verify_webhook
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Crear Blueprint para las vistas principales
main = Blueprint('main', __name__)

@main.route("/webhook", methods=["GET", "POST"])
def webhook():
    """
    Endpoint principal para el webhook de WhatsApp.
    GET: Verifica el webhook cuando WhatsApp lo solicita.
    POST: Procesa mensajes entrantes de WhatsApp.
    """
    if request.method == "GET":
        return verify_webhook(request)
    
    elif request.method == "POST":
        return handle_webhook(request)

@main.route("/health", methods=["GET"])
def health_check():
    """
    Endpoint para verificar el estado de la aplicación.
    Útil para monitoreo y comprobaciones de disponibilidad.
    """
    return jsonify({
        "status": "ok",
        "version": os.getenv("APP_VERSION", "1.0.0")
    })

# Blueprint para admin (se puede expandir en el futuro)
admin = Blueprint('admin', __name__, url_prefix='/admin')

@admin.route("/stats", methods=["GET"])
def stats():
    """
    Endpoint para mostrar estadísticas de uso.
    Se puede proteger con autenticación en el futuro.
    """
    # Implementar estadísticas básicas
    # En una versión más avanzada, esto podría conectarse a una base de datos
    stats_data = {
        "total_messages": 0,  # Conectar a DB para datos reales
        "active_users": 0,
        "response_time_avg": "0ms"
    }
    return jsonify(stats_data)

# Se pueden agregar más blueprints para otras funcionalidades