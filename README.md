<p align="center">
  <img src="assets/argus-icon-premium.png" alt="ARGUS logo" width="220" />
</p>

# ARGUS

CLI de OSINT com coleta por username e email, validação HTTP e análise opcional por IA.

## Setup

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -e .
```

## Uso

```bash
uv run argus version
uv run argus search --username gfcramos
uv run argus search --username gfcramos --format json
uv run argus search --email pessoa@dominio.com
```

## Dependências de coleta

`maigret` e `holehe` são instalados junto com o projeto e executados a partir do ambiente virtual ativo.

## Saída

Relatórios em `json` e `html` são salvos em `reports/`.
