# WhatsApp Bot con OpenAI

Este proyecto implementa un chatbot de WhatsApp que utiliza la API oficial de WhatsApp (Meta) para recibir y enviar mensajes, y la API de OpenAI para generar respuestas inteligentes.

## Características

- Integración con la API oficial de WhatsApp Business
- Generación de respuestas utilizando OpenAI
- Estructura modular y escalable
- Sistema de logging configurable

## Requisitos

- Python 3.8+
- Una cuenta de Meta para desarrolladores con acceso a la API de WhatsApp Business
- Una cuenta de OpenAI con acceso a la API y un asistente configurado
- Ngrok o similar para exponer el webhook localmente (durante desarrollo)

## Instalación

1. Clonar el repositorio:
   ```
   git clone https://github.com/CarlosChiguichon/whatsapp-bot-python-v2.git
   cd whatsapp-bot
   ```

2. Crear un entorno virtual e instalar dependencias:
   ```
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Copiar el archivo .env.example a .env y configurar las variables de entorno:
   ```
   cp .env.example .env
   ```

4. Editar el archivo .env con tus credenciales y configuraciones.

## Configuración

El proyecto utiliza variables de entorno para la configuración. Estas son las variables requeridas:

- `WHATSAPP_TOKEN`: Token de acceso a la API de WhatsApp
- `WHATSAPP_VERIFY_TOKEN`: Token de verificación para el webhook de WhatsApp
- `WHATSAPP_APP_SECRET`: App Secret de WhatsApp para verificar firmas
- `PHONE_NUMBER_ID`: ID del número de teléfono en WhatsApp Business
- `OPENAI_API_KEY`: API Key de OpenAI
- `OPENAI_ASSISTANT_ID`: ID del asistente configurado en OpenAI
- `PORT`: Puerto para la aplicación (por defecto: 3000)
- `DEBUG`: Modo debug (True/False)

## Uso

1. Iniciar la aplicación:
   ```
   python -m app.main
   ```

2. Exponer el webhook utilizando ngrok o similar:
   ```
   ngrok http 3000
   ```

3. Configurar la URL del webhook en el panel de Meta for Developers:
   ```
   https://tu-dominio-ngrok.ngrok.io/webhook
   ```

## Estructura del proyecto

```
whatsapp-bot/
├── .env                      # Variables de entorno
├── .gitignore                # Archivos a ignorar por git
├── README.md                 # Documentación del proyecto
├── requirements.txt          # Dependencias del proyecto
├── config/                   # Configuraciones
├── app/                      # Código principal
│   ├── main.py               # Punto de entrada
│   ├── whatsapp/             # Módulo de WhatsApp
│   ├── openai/               # Módulo de OpenAI
│   ├── services/             # Servicios de negocio
│   └── utils/                # Utilidades
└── tests/                    # Pruebas
```

## Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue primero para discutir los cambios que te gustaría realizar.

## Licencia

[MIT](LICENSE)