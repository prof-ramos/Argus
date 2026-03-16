# ARGUS — OSINT Suite com IA

OSINT Suite profissional com coleta paralela, validação HTTP e análise comportamental via IA.

## Funcionalidades

- Coleta paralela: Maigret (username) + Holehe (email)
- Filtro anti-falso-positivo com validação HTTP real
- Enriquecimento com metadados de plataformas
- Análise comportamental com GPT-4o-mini
- Output: CLI (tabela Rich), JSON, HTML

## Requisitos

- Python 3.10+
- OpenAI API Key (apenas para `--ai`)

## Instalação

```bash
git clone <seu-repo> argus
cd argus
bash install.sh
```

Ou manualmente:

```bash
pip install -e .
pip install maigret==0.3.7 holehe==1.0.1
cp .env.example .env
# edite .env com sua OpenAI API Key
```

## Configuração

Edite o arquivo `.env`:

```env
OPENAI_API_KEY=sk-...        # obrigatório para --ai
ARGUS_OUTPUT_DIR=./reports   # pasta de saída dos relatórios
VALIDATE_URLS=true           # validação HTTP anti-falso-positivo
COLLECTOR_TIMEOUT=15         # timeout dos coletores (segundos)
```

## Uso

```bash
# Busca por username (saída CLI)
argus --username johndoe

# Busca por email
argus --email john@example.com

# Busca combinada com análise de IA
argus --username johndoe --email john@example.com --ai

# Salvar relatório JSON
argus --username johndoe --format json

# Gerar e abrir relatório HTML
argus --username johndoe --ai --format html --open

# Ver versão
argus version
```

## Estrutura do Projeto

```
argus/
├── argus.py                  # CLI principal (Typer)
├── config/
│   ├── settings.py           # variáveis de ambiente
│   └── platforms_metadata.json
├── collectors/
│   ├── maigret.py            # busca por username
│   └── holehe.py             # busca por email
├── processing/
│   ├── normalizer.py         # deduplicação
│   ├── filter.py             # validação HTTP
│   └── enricher.py           # metadados de plataformas
├── ai/
│   ├── prompt_builder.py
│   └── report_generator.py   # integração OpenAI
├── output/
│   └── formatter.py          # CLI / JSON / HTML
└── tests/
    └── e2e/                  # 46 testes E2E
```

## Testes

```bash
pytest tests/e2e/ -v
```

## Pipeline

```
Input (username / email)
    ↓
Coleta paralela (Maigret + Holehe)
    ↓
Normalização + Deduplicação
    ↓
Filtro anti-falso-positivo (HTTP)
    ↓
Enriquecimento (metadados)
    ↓
Análise IA (opcional)
    ↓
Output (CLI / JSON / HTML)
```

---

Criado para investigação responsável de presença digital pública.
