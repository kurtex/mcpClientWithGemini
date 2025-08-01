#!/bin/bash
# Este script analiza las dependencias del proyecto en busca de vulnerabilidades conocidas.
set -e

# --- Configuración ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
REQUIREMENTS_FILE="$SCRIPT_DIR/client_requirements.txt"

# --- Script Principal ---
echo "--- Auditoría de Seguridad de Dependencias ---"

# 1. Asegurarse de que el entorno virtual y las dependencias están listos.
# (Esta lógica es similar a la de run_client.sh para ser autocontenido)
if [ ! -d "$VENV_DIR" ] || [ "$REQUIREMENTS_FILE" -nt "$VENV_DIR" ]; then
    echo "Configurando/Actualizando el entorno virtual para la auditoría..."
    rm -rf "$VENV_DIR"
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install -r "$REQUIREMENTS_FILE"
fi

# 2. Ejecutar pip-audit usando el intérprete del entorno virtual.
PYTHON_EXEC="$VENV_DIR/bin/python3"
if [ ! -f "$PYTHON_EXEC" ]; then
    PYTHON_EXEC="$VENV_DIR/bin/python"
fi

echo "Ejecutando auditoría..."
echo "---------------------"

# Usamos -v para obtener un informe detallado.
# El comando saldrá con un código de error si se encuentran vulnerabilidades.
"$PYTHON_EXEC" -m pip_audit -v

echo "---------------------"
echo "Auditoría completada. Si no se mostraron vulnerabilidades, ¡estás a salvo!"
