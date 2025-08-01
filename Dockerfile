FROM python:3.11-slim

WORKDIR /app

COPY mcp_server_gemini.py .

RUN pip install --no-cache-dir google-generativeai websockets

# Esta variable se puede sobreescribir al ejecutar el contenedor
ENV GEMINI_API_KEY=""

RUN useradd -m appuser
USER appuser

CMD ["python", "mcp_server_gemini.py"]
