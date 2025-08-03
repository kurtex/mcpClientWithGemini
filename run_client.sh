#!/bin/bash
# Script de ejecución y configuración todo-en-uno (Versión final y robusta).

set -e

# --- Configuración de rutas ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
REQUIREMENTS_FILE="$SCRIPT_DIR/client_requirements.txt"
PIP_STAMP_FILE="$VENV_DIR/.pip_installed" # Archivo marcador para la instalación

# --- Creación del archivo de requisitos si no existe ---
# Solo se crea si no está presente, para no sobreescribir cambios manuales.
if [ ! -f "$REQUIREMENTS_FILE" ]; then
    echo "Creando archivo de dependencias 'client_requirements.txt' por primera vez..."
    printf "%s\n" "websockets" "python-dotenv" > "$REQUIREMENTS_FILE"
fi

# --- Creación/Actualización del entorno virtual y dependencias ---
# Solo se (re)instala si el venv no existe, el marcador falta o los requisitos son más recientes.
if [ ! -d "$VENV_DIR" ] || [ ! -f "$PIP_STAMP_FILE" ] || [ "$REQUIREMENTS_FILE" -nt "$PIP_STAMP_FILE" ]; then
    echo "Creando/Actualizando el entorno virtual..."
    rm -rf "$VENV_DIR"
    python3 -m venv "$VENV_DIR"
    echo "Instalando dependencias..."
    "$VENV_DIR/bin/pip" install -r "$REQUIREMENTS_FILE"
    echo "Instalación completada."
    touch "$PIP_STAMP_FILE" # Se crea/actualiza el archivo marcador
else
    echo "El entorno virtual y las dependencias ya están actualizados."
fi

# --- Búsqueda del intérprete de Python correcto ---
PYTHON_EXEC="$VENV_DIR/bin/python"
if [ ! -f "$PYTHON_EXEC" ]; then
    echo "ERROR CRÍTICO: No se encontró el intérprete de Python en: $PYTHON_EXEC"
    exit 1
fi

# --- Ejecución final ---
echo "-------------------------"
echo "Lanzando la aplicación..."
"$PYTHON_EXEC" "$SCRIPT_DIR/mcp_client_gemini.py"

