# ARGUS — OSINT Suite com IA

<p align="center">
  <img src="assets/icon-1773681351396.png" alt="ARGUS Logo" width="400"/>
</p>

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
argus search --username johndoe

# Busca por email
argus search --email john@example.com

# Busca combinada com análise de IA
argus search --username johndoe --email john@example.com --ai

# Salvar relatório JSON
argus search --username johndoe --format json

# Gerar e abrir relatório HTML
argus search --username johndoe --ai --format html --open

# Ver versão
argus version
```

## Estrutura do Projeto

```mermaid
graph TD
    ROOT["argus/"]

    ROOT --> ARGUS["argus.py<br/>CLI principal (Typer)"]
    ROOT --> CONFIG["config/"]
    ROOT --> COLLECTORS["collectors/"]
    ROOT --> PROCESSING["processing/"]
    ROOT --> AI["ai/"]
    ROOT --> OUTPUT["output/"]
    ROOT --> TESTS["tests/"]

    CONFIG --> SETTINGS["settings.py<br/>variáveis de ambiente"]
    CONFIG --> METADATA["platforms_metadata.json"]

    COLLECTORS --> MAIGRET["maigret.py<br/>busca por username"]
    COLLECTORS --> HOLEHE["holehe.py<br/>busca por email"]

    PROCESSING --> NORMALIZER["normalizer.py<br/>deduplicação"]
    PROCESSING --> FILTER["filter.py<br/>validação HTTP"]
    PROCESSING --> ENRICHER["enricher.py<br/>metadados"]

    AI --> PROMPT["prompt_builder.py"]
    AI --> GEN["report_generator.py<br/>integração OpenAI"]

    OUTPUT --> FORMATTER["formatter.py<br/>CLI / JSON / HTML"]

    TESTS --> E2E["e2e/<br/>48 testes E2E"]

    style ROOT fill:#1565c0,color:#fff
    style CONFIG fill:#42a5f5,color:#fff
    style COLLECTORS fill:#ff9800,color:#fff
    style PROCESSING fill:#4caf50,color:#fff
    style AI fill:#9c27b0,color:#fff
    style OUTPUT fill:#00bcd4,color:#fff
    style TESTS fill:#ff5722,color:#fff
```

## Testes

```bash
pytest tests/e2e/ -v
```

## Pipeline

```mermaid
graph LR
    A[Input<br/>username / email] --> B[Coleta Paralela<br/>Maigret + Holehe]
    B --> C[Normalização<br/>+ Deduplicação]
    C --> D[Filtro Anti-FP<br/>Validação HTTP]
    D --> E[Enriquecimento<br/>Metadados]
    E --> F[Análise IA<br/>opcional]
    E --> G[Output<br/>CLI / JSON / HTML]
    F --> G

    style A fill:#e3f2fd
    style B fill:#fff3e0
    style C fill:#f3e5f5
    style D fill:#e8f5e9
    style E fill:#fff3e0
    style F fill:#fce4ec
    style G fill:#e1f5ff
```

---

Criado para investigação responsável de presença digital pública.
