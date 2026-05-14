#!/bin/bash
# Script para Windows que baixa e executa o setup
# Salve como: install.bat

@echo off
chcp 65001 >nul
echo.
echo  ╔════════════════════════════════════════════════════════════╗
echo  ║    🎲 MONTE CARLO PRO - Instalador Automático             ║
echo  ║          Versão 2.0                                       ║
echo  ╚════════════════════════════════════════════════════════════╝
echo.

REM Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ✗ Python não encontrado!
    echo ℹ Baixe em: https://www.python.org/downloads/
    echo   (Marque a opção: Add Python to PATH durante instalação)
    pause
    exit /b 1
)

echo ✓ Python encontrado
echo.
echo ℹ Iniciando download e configuração...
echo ℹ Isso pode levar alguns minutos na primeira vez
echo.

REM Download do setup.py
echo Baixando script de instalação...
curl -L -o setup.py https://raw.githubusercontent.com/leandrotpaixao/program/main/setup.py
if errorlevel 1 (
    echo ✗ Erro ao baixar arquivo
    pause
    exit /b 1
)

echo.
echo ✓ Arquivo baixado com sucesso
echo.
echo Executando instalação...
echo.

REM Executar setup.py
python setup.py
pause
