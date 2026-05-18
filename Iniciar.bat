@echo off
title Extractor de Trades - Iniciando...

:: ── Verificar si Python está instalado ──────────────────────
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  ╔══════════════════════════════════════════════════╗
    echo  ║         Python no está instalado                 ║
    echo  ║                                                  ║
    echo  ║  Se va a abrir el instalador oficial de Python.  ║
    echo  ║                                                  ║
    echo  ║  IMPORTANTE: durante la instalacion, tilda la   ║
    echo  ║  opcion "Add Python to PATH" antes de continuar  ║
    echo  ║                                                  ║
    echo  ║  Una vez instalado, cerrá esta ventana y volvé   ║
    echo  ║  a hacer doble click en Iniciar.bat              ║
    echo  ╚══════════════════════════════════════════════════╝
    echo.
    pause
    start https://www.python.org/downloads/
    exit /b 0
)

:: ── Python encontrado, lanzar instalador visual ─────────────
cd /d "%~dp0"
python installer.py
if %errorlevel% neq 0 (
    echo.
    echo  ERROR al lanzar el instalador. Detalle arriba.
    pause
)
