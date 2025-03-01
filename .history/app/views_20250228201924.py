from flask import Blueprint, request, jsonify, current_app
import logging
from app.utils.whatsapp_utils import process_whatsapp_message, is_valid_whatsapp_message

# Crear un blueprint para las rutas
webhook_blueprint = Blueprint('webhook', __name__)

# Configurar logger
logger = logging.getLogger(__name__)

@webhook_blueprint.route("/webhook", methods=["GET", "POST"])
def webhook():
    """
    Endpoint para el webhook de WhatsApp.
    Maneja tanto las verificaciones (GET) como los mensajes entrantes (POST).
    """
    # Maneja la verificación del webhook de WhatsApp (GET)
    if request.method == "GET":
        verify_token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        
        if verify_token == current_app.config["VERIFY_TOKEN"]:
            logger.info("Webhook verification successful")
            return challenge
        else:
            logger.warning(f"Webhook verification failed: invalid token {verify_token}")
            return "Verification token mismatch", 403

    # Maneja los mensajes entrantes de WhatsApp (POST)
    # Nota: Solo validamos la firma en producción
    flask_env = current_app.config.get("FLASK_ENV", "production")
    if flask_env != "development":
        from app.decorators.security import validate_signature
        signature = request.headers.get("X-Hub-Signature-256", "")[7:]  # Removing 'sha256='
        
        if not signature or not validate_signature(request.data.decode("utf-8"), signature):
            logger.warning("Signature verification failed!")
            return jsonify({"status": "error", "message": "Invalid signature"}), 403

    # Continuar con el procesamiento normal
    data = request.get_json()
    
    if not data:
        logger.warning("Received empty payload")
        return jsonify({"status": "error", "message": "Empty payload"}), 400
    
    try:
        # Si es un mensaje de WhatsApp
        if is_valid_whatsapp_message(data):
            # Procesar en un contexto protegido para evitar fallos
            try:
                process_whatsapp_message(data)
            except Exception as e:
                logger.error(f"Error processing WhatsApp message: {str(e)}")
                # No fallar la respuesta aunque el procesamiento falle
        
        # Responder con éxito a Meta para confirmar recepción
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        logger.error(f"Error in webhook: {str(e)}")
        # Aún así, confirmar recepción para evitar reintentos
        return jsonify({"status": "error", "message": str(e)}), 200

@webhook_blueprint.route("/", methods=["GET"])
def health_check():
    """
    Endpoint simple para verificar que la aplicación está en ejecución.
    """
    return jsonify({
        "status": "online",
        "service": "WhatsApp Bot",
        "version": "1.0.0"
    })