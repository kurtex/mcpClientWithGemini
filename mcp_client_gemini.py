import asyncio
import websockets
import json
import os
import ssl
import pathlib
from dotenv import load_dotenv

class MCPClient:
    def __init__(self, uri: str, token: str = None, ssl_context: ssl.SSLContext = None):
        self.uri = uri
        self.token = token
        self.connection = None
        self.conversation_history = []
        self.ssl_context = ssl_context

    async def connect(self):
        try:
            self.connection = await websockets.connect(self.uri, ssl=self.ssl_context)
            print("Conectado al servidor MCP. Escribe 'salir' o 'exit' para terminar.")
        except websockets.exceptions.ConnectionClosed as e:
            print(f"[ERROR] No se pudo conectar. El servidor cerró la conexión: {e.reason}")
            self.connection = None
        except ConnectionRefusedError:
            print(f"[ERROR] Conexión rechazada en {self.uri}. Asegúrate de que el servidor esté en ejecución.")
            self.connection = None
        except ssl.SSLError as e:
            print(f"[ERROR] Fallo de SSL/TLS: {e}. Asegúrate de que el certificado del servidor es válido y que estás usando 'wss'.")
            self.connection = None

    def add_to_history(self, role: str, text: str):
        self.conversation_history.append({"role": role, "parts": [{"text": text}]})

    async def send_history(self, metadata: dict = {}):
        if not self.connection:
            return
        
        message = {
            "type": "prompt",
            "content": self.conversation_history,
            "metadata": metadata
        }
        if self.token:
            message["token"] = self.token
            
        try:
            await self.connection.send(json.dumps(message))
        except websockets.exceptions.ConnectionClosed as e:
            print(f"\n[ERROR] La conexión se cerró. Razón: {e.reason}")
            self.connection = None


    async def receive_response(self):
        if not self.connection:
            return ""

        print("\nModelo:")
        full_text = ""
        while True:
            try:
                response = await self.connection.recv()
                data = json.loads(response)
                if data.get("type") == "response":
                    print()
                    break
                elif data.get("type") == "stream":
                    content = data.get("content", "")
                    print(content, end="", flush=True)
                    full_text += content
                elif data.get("type") == "error":
                    print(f"\n[ERROR DEL SERVIDOR] {data.get('message')}")
                    break
                else:
                    print(f"[DEBUG] Mensaje no reconocido: {data}")
            except websockets.exceptions.ConnectionClosed as e:
                print(f"\n[ERROR] Conexión cerrada por el servidor. Razón: {e.reason}")
                self.connection = None
                break
        
        if full_text:
            self.add_to_history("model", full_text)
        return full_text

    async def close(self):
        if self.connection:
            await self.connection.close()
            print("Conexión cerrada.")

async def main():
    # Load environment variables from .env file
    load_dotenv()
    token = os.getenv("MCP_SERVER_TOKEN")
    if not token:
        print("[AVISO] MCP_SERVER_TOKEN no está definida. La conexión podría ser rechazada por el servidor.")

    # Setup SSL context for WSS
    cert_path = pathlib.Path(__file__).parent / "certs/cert.pem"
    if cert_path.exists():
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_context.load_verify_locations(cert_path)
        uri = "wss://localhost:8080"
        print("Certificado encontrado. Usando wss.")
    else:
        ssl_context = None
        uri = "ws://localhost:8080"
        print("[AVISO] Certificado no encontrado. Usando ws (no seguro).")


    client = MCPClient(uri, token, ssl_context=ssl_context)
    await client.connect()

    if not client.connection:
        return

    try:
        while True:
            try:
                if not client.connection:
                    print("Se ha perdido la conexión con el servidor.")
                    break
                
                prompt = input("\nTú: ")
                if prompt.lower() in ["salir", "exit"]:
                    break
                
                client.add_to_history("user", prompt)
                await client.send_history()
                await client.receive_response()

            except (KeyboardInterrupt, EOFError):
                break
    finally:
        await client.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCliente terminado.")