<p align="center">
  <img src="assets/argus-icon-premium.png" alt="ARGUS logo" width="220" />
</p>

# ARGUS

CLI de OSINT com coleta por username e email, validação HTTP e análise opcional por IA.

## Funcionalidades

- Coleta por username com `maigret`
- Coleta por email com `holehe`
- Filtro anti-falso-positivo com validação HTTP
- Enriquecimento com metadados por plataforma
- Saída em CLI, JSON e HTML
- Análise opcional com OpenAI via `--ai`

## Setup

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -e .
cp .env.example .env
```

## Uso

```bash
uv run argus version
uv run argus search --username gfcramos
uv run argus search --username gfcramos --format json
uv run argus search --email pessoa@dominio.com
uv run argus search --username gfcramos --ai --api-key sk-...
```

## Configuração

Variáveis principais em `.env.example`:

```env
OPENAI_API_KEY=sk-...
ARGUS_OUTPUT_DIR=./reports
COLLECTOR_TIMEOUT=30
MAIGRET_TOP_SITES=20
VALIDATE_URLS=true
```

## Dependências de coleta

`maigret` e `holehe` são instalados junto com o projeto e executados a partir do ambiente virtual ativo.

## Saída

Relatórios em `json` e `html` são salvos em `reports/`.

## Testes

```bash
uv run pytest tests/e2e -q
```

## Estrutura

```text
argus.py
collectors/
processing/
ai/
output/
config/
tests/e2e/
```
