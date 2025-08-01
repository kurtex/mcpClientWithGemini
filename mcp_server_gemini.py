import asyncio
import websockets
import os
import json
import ssl
import logging
import time
from collections import deque

# --- Security & Configuration ---
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] [%(asctime)s] %(message)s')

# Rate Limiting: 10 requests per 60 seconds per client.
RATE_LIMIT_REQUESTS = 10
RATE_LIMIT_SECONDS = 60
# Input Validation: Max 100,000 characters for the conversation history.
MAX_HISTORY_SIZE = 100_000

# Dictionary to store client request timestamps for rate limiting.
client_requests = {}

# --- Gemini Model Setup ---
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ModuleNotFoundError:
    logging.warning("El módulo 'google-generativeai' no está disponible. El servidor no podrá procesar prompts.")
    GEMINI_AVAILABLE = False

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MCP_SERVER_TOKEN = os.getenv("MCP_SERVER_TOKEN")

if not GEMINI_API_KEY:
    logging.warning("GEMINI_API_KEY no definida. El servidor no podrá conectarse a Gemini.")
if not MCP_SERVER_TOKEN:
    logging.warning("MCP_SERVER_TOKEN no definida. El servidor se ejecutará sin autenticación.")

model = None
if GEMINI_AVAILABLE and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash")
        logging.info("Modelo Gemini configurado exitosamente.")
    except Exception as config_error:
        logging.error(f"No se pudo configurar el modelo Gemini: {config_error}")

# --- Helper Functions ---
def is_rate_limited(client_ip: str) -> bool:
    """Checks if a client has exceeded the rate limit."""
    current_time = time.time()
    
    # Get the list of timestamps for the client, or create a new one.
    timestamps = client_requests.get(client_ip, deque())
    
    # Remove timestamps older than the limit window.
    while timestamps and timestamps[0] <= current_time - RATE_LIMIT_SECONDS:
        timestamps.popleft()
    
    # If the number of requests is over the limit, deny the request.
    if len(timestamps) >= RATE_LIMIT_REQUESTS:
        return True
    
    # Record the new request timestamp and update the client's record.
    timestamps.append(current_time)
    client_requests[client_ip] = timestamps
    return False

# --- WebSocket Handler ---
async def handle_connection(websocket):
    client_ip = websocket.remote_address[0]
    logging.info(f"Cliente conectado desde {client_ip}. Esperando autenticación.")

    try:
        auth_message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
        auth_data = json.loads(auth_message)
        if MCP_SERVER_TOKEN and auth_data.get("token") != MCP_SERVER_TOKEN:
            logging.warning(f"Fallo de autenticación desde {client_ip}.")
            await websocket.close(code=1008, reason="Authentication failed")
            return
    except (asyncio.TimeoutError, json.JSONDecodeError):
        logging.warning(f"No se recibió la autenticación a tiempo desde {client_ip}.")
        await websocket.close(code=1008, reason="Authentication required")
        return
    except websockets.exceptions.ConnectionClosed:
        logging.info(f"Conexión cerrada por {client_ip} antes de la autenticación.")
        return

    logging.info(f"Cliente {client_ip} autenticado. Esperando prompts.")
    try:
        async for message in websocket:
            # --- Security Check: Rate Limiting ---
            if is_rate_limited(client_ip):
                logging.warning(f"Cliente {client_ip} ha excedido el límite de peticiones.")
                await websocket.send(json.dumps({"type": "error", "message": "Límite de peticiones excedido. Inténtalo más tarde."}))
                continue

            try:
                # --- Security Check: Input Validation ---
                try:
                    data = json.loads(message)
                    if not isinstance(data, dict) or data.get("type") != "prompt" or "content" not in data:
                        raise ValueError("El JSON recibido es inválido o no tiene el formato esperado.")
                    
                    history_str = json.dumps(data["content"])
                    if len(history_str) > MAX_HISTORY_SIZE:
                        raise ValueError(f"El historial de la conversación excede el tamaño máximo de {MAX_HISTORY_SIZE} caracteres.")
                except (json.JSONDecodeError, ValueError) as e:
                    logging.warning(f"Validación de entrada fallida para {client_ip}: {e}")
                    await websocket.send(json.dumps({"type": "error", "message": str(e)}))
                    continue

                if not model:
                    await websocket.send(json.dumps({"type": "error", "message": "El servidor no está configurado para responder."}))
                    continue

                conversation_history = data.get("content", [])
                if not conversation_history:
                    continue

                metadata = data.get("metadata", {})
                
                stream = model.generate_content(conversation_history, stream=True, **metadata)
                for chunk in stream:
                    if hasattr(chunk, 'text') and chunk.text:
                        await websocket.send(json.dumps({"type": "stream", "content": chunk.text}))
                await websocket.send(json.dumps({"type": "response", "content": "[FINISHED]"}))

            except Exception as e:
                logging.error(f"Ocurrió un error procesando el mensaje de {client_ip}: {e}", exc_info=True)
                if websocket.is_open:
                    await websocket.send(json.dumps({"type": "error", "message": "Ocurrió un error interno del servidor."}))

    except websockets.exceptions.ConnectionClosed as e:
        logging.info(f"La conexión con {client_ip} se cerró inesperadamente: {e}")
    finally:
        logging.info(f"Cliente {client_ip} desconectado.")

# --- Main Execution ---
async def main():
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    cert_path = 'certs/cert.pem'
    key_path = 'certs/key.pem'

    try:
        ssl_context.load_cert_chain(cert_path, key_path)
        server_args = {"ssl": ssl_context}
        protocol = "wss"
    except FileNotFoundError:
        server_args = {}
        protocol = "ws"
        logging.warning("Certificado no encontrado. Iniciando en modo no seguro (ws).")

    logging.info(f"Servidor MCP activo en {protocol}://0.0.0.0:8080")
    
    async with websockets.serve(
        handle_connection,
        "0.0.0.0",
        8080,
        max_size=MAX_HISTORY_SIZE + 1024, # Permitir un poco más del máximo para la estructura del JSON.
        ping_interval=None,
        ping_timeout=None,
        **server_args
    ):
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Servidor detenido por el usuario.")
