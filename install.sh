#!/bin/bash
# Script para Linux/Mac que baixa e executa o setup
# Salve como: install.sh ou execute: bash install.sh

#!/bin/bash

echo ""
echo "  ╔════════════════════════════════════════════════════════════╗"
echo "  ║    🎲 MONTE CARLO PRO - Instalador Automático             ║"
echo "  ║          Versão 2.0                                       ║"
echo "  ╚════════════════════════════════════════════════════════════╝"
echo ""

# Verificar se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "✗ Python 3 não encontrado!"
    echo "ℹ Instale com: sudo apt-get install python3 python3-pip (Ubuntu/Debian)"
    echo "              brew install python3 (Mac)"
    exit 1
fi

echo "✓ Python encontrado: $(python3 --version)"
echo ""
echo "ℹ Iniciando download e configuração..."
echo "ℹ Isso pode levar alguns minutos na primeira vez"
echo ""

# Download do setup.py
echo "Baixando script de instalação..."
if command -v curl &> /dev/null; then
    curl -L -o setup.py https://raw.githubusercontent.com/leandrotpaixao/program/main/setup.py
elif command -v wget &> /dev/null; then
    wget -O setup.py https://raw.githubusercontent.com/leandrotpaixao/program/main/setup.py
else
    echo "✗ Erro: curl ou wget não encontrados"
    exit 1
fi

if [ ! -f setup.py ]; then
    echo "✗ Erro ao baixar arquivo"
    exit 1
fi

echo ""
echo "✓ Arquivo baixado com sucesso"
echo ""
echo "Executando instalação..."
echo ""

# Executar setup.py
python3 setup.py
