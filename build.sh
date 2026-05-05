#!/bin/bash
# Krvo - Script de Build para Linux/Mac
# ======================================
#
# Uso:
#   ./build.sh           - Build padrão (pasta)
#   ./build.sh onefile   - Executável único
#   ./build.sh debug     - Com console de debug
#
# Requisitos:
#   pip install pyinstaller customtkinter requests

echo ""
echo "========================================"
echo "   KRVO - Build para Linux/Mac"
echo "========================================"
echo ""

# Verifica Python
if ! command -v python3 &> /dev/null; then
    echo "[ERRO] Python3 não encontrado!"
    exit 1
fi

# Verifica/instala PyInstaller
python3 -c "import PyInstaller" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[INFO] Instalando PyInstaller..."
    pip3 install pyinstaller
fi

# Instala dependências
echo "[INFO] Instalando dependências..."
pip3 install -r requirements.txt -q

# Limpa builds anteriores
echo "[INFO] Limpando builds anteriores..."
rm -rf dist/ build/pyinstaller/

# Argumentos
ONEFILE=""
CONSOLE="--noconsole"

if [ "$1" == "onefile" ]; then
    ONEFILE="--onefile"
fi

if [ "$1" == "debug" ] || [ "$2" == "debug" ]; then
    CONSOLE="--console"
fi

# Build
echo "[INFO] Gerando executável..."
echo ""

python3 -m PyInstaller \
    --name "Krvo" \
    --windowed \
    $CONSOLE \
    $ONEFILE \
    --add-data "src:src" \
    --add-data "assets:assets" \
    --hidden-import customtkinter \
    --hidden-import tkinter \
    --hidden-import requests \
    --hidden-import json \
    --hidden-import threading \
    --hidden-import webbrowser \
    --hidden-import pathlib \
    --hidden-import dataclasses \
    --collect-all customtkinter \
    --noconfirm \
    --clean \
    krvo.py

if [ $? -ne 0 ]; then
    echo ""
    echo "[ERRO] Build falhou!"
    exit 1
fi

echo ""
echo "========================================"
echo "   BUILD CONCLUÍDO!"
echo "========================================"
echo ""
echo "Executável gerado em: dist/Krvo/"
echo ""
echo "Para distribuir, compacte a pasta dist/Krvo"
echo ""
