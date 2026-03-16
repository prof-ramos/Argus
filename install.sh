#!/usr/bin/env bash
set -e

echo "=== ARGUS — Instalação ==="

# Verifica Python 3.10+
PYTHON=$(command -v python3 || command -v python)
PY_VERSION=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$($PYTHON -c "import sys; print(sys.version_info.major)")
PY_MINOR=$($PYTHON -c "import sys; print(sys.version_info.minor)")

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
    echo "Erro: Python 3.10+ necessário (encontrado: $PY_VERSION)"
    exit 1
fi
echo "Python $PY_VERSION OK"

# Instala o pacote principal
echo ""
echo "Instalando dependências principais..."
pip install -e . --quiet

# Instala coletores externos
echo "Instalando maigret e holehe..."
pip install maigret==0.3.7 holehe==1.0.1 --quiet

# Cria .env se não existir
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo ""
    echo "Arquivo .env criado a partir de .env.example"
    echo "IMPORTANTE: edite .env e insira sua OPENAI_API_KEY para usar --ai"
else
    echo ".env já existe, mantido sem alterações"
fi

# Cria pasta de relatórios
mkdir -p reports

echo ""
echo "=== Instalação concluída ==="
echo ""
echo "Próximos passos:"
echo "  1. Edite .env com sua OpenAI API Key (opcional, apenas para --ai)"
echo "  2. argus --username seu-usuario"
echo "  3. argus --username seu-usuario --ai --format html --open"
echo ""
echo "Para rodar os testes:"
echo "  pytest tests/e2e/ -v"
