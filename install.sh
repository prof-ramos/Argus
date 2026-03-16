#!/usr/bin/env bash
set -e

echo "=== ARGUS — Instalação ==="

# Verifica Python 3.10+
PYTHON=$(command -v python3 || command -v python)
PY_MAJOR=$($PYTHON -c "import sys; print(sys.version_info.major)")
PY_MINOR=$($PYTHON -c "import sys; print(sys.version_info.minor)")
PY_VERSION="$PY_MAJOR.$PY_MINOR"

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
    echo "Erro: Python 3.10+ necessário (encontrado: $PY_VERSION)"
    exit 1
fi
echo "Python $PY_VERSION OK"

# Instala o pacote principal (sem maigret/holehe que têm deps problemáticas)
echo ""
echo "Instalando dependências principais..."
pip install \
    requests aiohttp httpx click rich typer \
    openai pydantic python-dotenv tqdm colorama \
    --quiet

# Instala dependências de runtime do maigret antecipadamente
# (evita erros de módulos faltando na primeira execução)
echo "Instalando dependências de suporte aos coletores..."
pip install \
    aiodns alive-progress python-socks aiohttp-socks \
    xmind pycountry mock future socid-extractor \
    --quiet 2>/dev/null || true

# Instala maigret (sem deps, pois já instalamos acima)
echo "Instalando maigret..."
pip install maigret --no-deps --quiet 2>/dev/null || \
pip install maigret --quiet 2>/dev/null || \
echo "  Aviso: maigret não pôde ser instalado automaticamente."

# Instala holehe (deps nativas podem falhar em alguns sistemas)
echo "Instalando holehe..."
pip install holehe --quiet 2>/dev/null || (
    echo "  Tentando instalação alternativa do holehe..."
    pip install holehe --no-deps --quiet 2>/dev/null && \
    pip install requests httpx freemail pyisemail pymysql \
        aiohttp asyncio click \
        --quiet 2>/dev/null
) || echo "  Aviso: holehe não pôde ser instalado. Busca por email desativada."

# Instala o ARGUS em modo editável
echo "Instalando ARGUS..."
pip install -e . --no-deps --quiet

# Cria .env se não existir
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo ""
    echo "Arquivo .env criado. Edite com sua OpenAI API Key para usar --ai:"
    echo "  nano .env"
else
    echo ".env já existe, mantido sem alterações."
fi

# Cria pasta de relatórios
mkdir -p reports

# Verifica se os coletores estão funcionais
echo ""
echo "Verificando coletores..."
$PYTHON -c "from maigret.maigret import main; print('  maigret OK')" 2>/dev/null || echo "  maigret: verificar instalação manual"
$PYTHON -c "import holehe; print('  holehe OK')" 2>/dev/null || echo "  holehe: verificar instalação manual"

echo ""
echo "=== Instalação concluída ==="
echo ""
echo "Uso:"
echo "  argus --username seu-usuario"
echo "  argus --username seu-usuario --ai --format html --open"
echo "  argus --email seu@email.com --ai"
echo ""
echo "Testes E2E:"
echo "  pip install pytest pytest-asyncio"
echo "  pytest tests/e2e/ -v"
