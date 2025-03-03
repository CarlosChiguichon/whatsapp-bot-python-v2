from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from app.whatsapp.handlers import handle_webhook, verify_webhook
from app.utils.logger import setup_logger

# Cargar variables de entorno
load_dotenv()

# Configurar logger
logger = setup_logger()

app = Flask(__name__)

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        return verify_webhook(request)
    
    elif request.method == "POST":
        return handle_webhook(request)

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"})

def start_app():
    port = int(os.getenv("PORT", 3000))
    debug = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    app.run(host="0.0.0.0", port=port, debug=debug)

if __name__ == "__main__":
    start_app()