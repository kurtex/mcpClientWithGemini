#!/bin/bash
# Script de ejecución y configuración todo-en-uno (Versión final y robusta).

set -e

# --- Configuración de rutas ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
REQUIREMENTS_FILE="$SCRIPT_DIR/client_requirements.txt"

# --- Creación/Corrección del archivo de requisitos ---
# Se sobrescribe cada vez para garantizar que siempre sea correcto.
echo "Asegurando la lista correcta de dependencias..."
printf "%s\n" "websockets" "python-dotenv" > "$REQUIREMENTS_FILE"

# --- Creación/Actualización del entorno virtual ---
# Solo se (re)crea el venv si no existe o si los requisitos han cambiado (lo cual es siempre, por el paso anterior).
if [ ! -d "$VENV_DIR" ] || [ "$REQUIREMENTS_FILE" -nt "$VENV_DIR" ]; then
    echo "Creando/Actualizando el entorno virtual..."
    rm -rf "$VENV_DIR"
    python3 -m venv "$VENV_DIR"
    echo "Instalando dependencias..."
    "$VENV_DIR/bin/pip" install -r "$REQUIREMENTS_FILE"
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

