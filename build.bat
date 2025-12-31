@echo off
REM Krvo - Script de Build para Windows
REM ====================================
REM
REM Uso:
REM   build.bat           - Build padrão (pasta)
REM   build.bat onefile   - Executável único
REM   build.bat debug     - Com console de debug
REM
REM Requisitos:
REM   pip install pyinstaller customtkinter requests

echo.
echo ========================================
echo   KRVO - Build para Windows
echo ========================================
echo.

REM Verifica Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado!
    exit /b 1
)

REM Verifica PyInstaller
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Instalando PyInstaller...
    pip install pyinstaller
)

REM Instala dependencias
echo [INFO] Instalando dependencias...
pip install -r requirements.txt -q

REM Limpa builds anteriores
echo [INFO] Limpando builds anteriores...
if exist dist rmdir /s /q dist
if exist build\pyinstaller rmdir /s /q build\pyinstaller

REM Argumentos
set ONEFILE=
set CONSOLE=--noconsole

if "%1"=="onefile" set ONEFILE=--onefile
if "%1"=="debug" set CONSOLE=--console
if "%2"=="debug" set CONSOLE=--console

REM Build
echo [INFO] Gerando executavel...
echo.

pyinstaller ^
    --name "Krvo" ^
    --windowed ^
    %CONSOLE% ^
    %ONEFILE% ^
    --icon "assets/krvo.ico" ^
    --add-data "src;src" ^
    --add-data "assets;assets" ^
    --hidden-import customtkinter ^
    --hidden-import tkinter ^
    --hidden-import requests ^
    --hidden-import json ^
    --hidden-import threading ^
    --hidden-import webbrowser ^
    --hidden-import pathlib ^
    --hidden-import dataclasses ^
    --collect-all customtkinter ^
    --noconfirm ^
    --clean ^
    krvo.py

if errorlevel 1 (
    echo.
    echo [ERRO] Build falhou!
    exit /b 1
)

echo.
echo ========================================
echo   BUILD CONCLUIDO!
echo ========================================
echo.
echo Executavel gerado em: dist\Krvo\
echo.
echo Para distribuir, compacte a pasta dist\Krvo
echo.

pause
