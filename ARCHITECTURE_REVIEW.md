# Revisão de Arquitetura — ARGUS

## 1. Avaliação da Estrutura Geral e Padrões

### Arquitetura: Pipeline em Camadas

O ARGUS segue uma arquitetura de **pipeline sequencial** bem definida:

```text
CLI (argus.py)
  → Collectors (maigret, holehe)
    → Processing (normalizer → filter → enricher)
      → AI (report_generator)
        → Output (formatter)
```

### Estrutura de Diretórios

```text
argus.py                    # Ponto de entrada CLI (Typer)
├── collectors/             # Coleta de dados OSINT
│   ├── base.py             # Modelo base (AccountResult, ResultStatus)
│   ├── maigret.py          # Busca por username
│   └── holehe.py           # Busca por email
├── processing/             # Pipeline de processamento
│   ├── normalizer.py       # Deduplicação
│   ├── filter.py           # Filtragem de falsos positivos
│   └── enricher.py         # Enriquecimento com metadados
├── ai/                     # Integração com LLM
│   ├── models.py           # Dataclass AIReport
│   ├── prompt_builder.py   # Construção de prompts
│   └── report_generator.py # Chamada OpenAI
├── output/                 # Formatação de saída
│   └── formatter.py        # CLI, JSON, HTML
└── config/                 # Configuração
    ├── settings.py          # Variáveis de ambiente
    └── platforms_metadata.json
```

### Padrões Identificados

| Padrão | Onde | Implementação |
|--------|------|---------------|
| **Pipeline/Chain** | `argus.py` | Estágios sequenciais de transformação |
| **Strategy** | `collectors/` | Collectors intercambiáveis com mesma interface async |
| **Lazy Init** | `ai/report_generator.py:17-23` | Cliente OpenAI criado sob demanda |
| **Builder** | `ai/prompt_builder.py` | Construção de prompts separada da execução |
| **Adapter** | `processing/enricher.py` | Transforma resultados com metadados externos |
| **Dataclass DTO** | `collectors/base.py`, `ai/models.py` | Objetos tipados vs dicts genéricos |

---

## 2. Problemas de Arquitetura Identificados

### P1 — Orquestração Monolítica no Entry Point (Severidade: Alta)

**Arquivo:** `argus.py:40-91`

O `argus.py` contém toda a lógica de orquestração inline dentro do handler do comando `search`. Coleta, processamento, IA e output estão todos acoplados em uma única função.

**Impacto:** Dificulta testes unitários da orquestração, impede reutilização programática (ex: uso como biblioteca), e mistura responsabilidades CLI com lógica de negócio.

```python
# Problema: tudo dentro do handler
@app.command()
def search(...):
    all_results = asyncio.run(collect())      # orquestração
    normalized = Normalizer.normalize(...)     # processamento
    filtered = asyncio.run(...)               # mais orquestração
    enriched = Enricher().enrich(...)         # mais processamento
    # ... output inline
```

**Sugestão:** Extrair uma classe `Pipeline` ou função `run_pipeline()` em módulo separado que encapsule o fluxo completo.

---

### P2 — Múltiplas Chamadas `asyncio.run()` (Severidade: Média)

**Arquivo:** `argus.py:50,55`

Há duas chamadas `asyncio.run()` no mesmo fluxo — uma para coleta e outra para filtragem. `asyncio.run()` cria e destrói um event loop a cada chamada, o que é ineficiente e pode causar problemas com recursos async compartilhados.

```python
all_results = asyncio.run(collect())           # loop 1
filtered = asyncio.run(FalsePositiveFilter().filter(normalized))  # loop 2
```

**Sugestão:** Consolidar em uma única coroutine `async def run_pipeline()` com um único `asyncio.run()`.

---

### P3 — Ausência de Interface/Protocolo para Collectors (Severidade: Média)

**Arquivos:** `collectors/maigret.py`, `collectors/holehe.py`

Os collectors compartilham a mesma interface (`async def collect(target) -> List[AccountResult]`) por convenção, mas não existe um `Protocol` ou classe abstrata que formalize isso.

**Impacto:** Nada impede um novo collector de desviar da interface esperada. O `argus.py` depende de um contrato implícito.

**Sugestão:** Criar um `Protocol` ou `ABC`:

```python
class Collector(Protocol):
    name: str
    async def collect(self, target: str) -> List[AccountResult]: ...
```

---

### P4 — Configuração com Side Effects no Import (Severidade: Média)

**Arquivo:** `config/settings.py:5,8-9`

O módulo executa `load_dotenv()` e `OUTPUT_DIR.mkdir()` como side effects no momento do import. Qualquer módulo que importe `settings` dispara criação de diretórios e leitura de `.env`.

```python
load_dotenv()                                    # side effect
OUTPUT_DIR = Path(os.getenv("ARGUS_OUTPUT_DIR", "./reports"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)   # side effect
```

**Impacto:** Dificulta testes (diretórios criados durante import) e torna o comportamento menos previsível.

**Sugestão:** Encapsular em uma função `init_config()` chamada explicitamente no entry point.

---

### P5 — Variável Duplicada (Severidade: Baixa)

**Arquivo:** `config/settings.py:11,23`

```python
ARGUS_LOG_LEVEL = os.getenv("ARGUS_LOG_LEVEL", "INFO")  # linha 11
LOG_LEVEL = os.getenv("ARGUS_LOG_LEVEL", "INFO")         # linha 23
```

Duas variáveis para a mesma configuração.

---

### P6 — Formatter Assumindo Estrutura de Dict Sem Validação (Severidade: Média)

**Arquivo:** `output/formatter.py:27-31,104`

O formatter acessa `r['url']`, `r['metadata']['category']` sem verificação. Se o enricher falhar parcialmente, isso causa `KeyError`.

```python
# HTML — sem fallback
f"""<a href="{html_lib.escape(r['url'])}">{html_lib.escape(r['url'])}</a>"""

# CLI — mesmo problema
table.add_row(r["site_name"], r["metadata"]["category"])
```

**Sugestão:** Usar `.get()` com valores padrão ou validar a estrutura antes da formatação.

---

### P7 — Versão Hardcoded (Severidade: Baixa)

**Arquivos:** `argus.py:97`, `pyproject.toml`

A versão está duplicada como string literal em `argus.py` e em `pyproject.toml`. Ao atualizar, é necessário editar em dois lugares.

**Sugestão:** Importar a versão de `pyproject.toml` via `importlib.metadata`.

---

### P8 — Limpeza de Temp Files Frágil (Severidade: Baixa)

**Arquivo:** `collectors/maigret.py:79-82`

A limpeza manual de arquivos temporários no `finally` é frágil. Se `output_dir.glob("*")` incluir subdiretórios, `rmdir()` falhará.

```python
finally:
    for file in output_dir.glob("*"):
        file.unlink(missing_ok=True)
    output_dir.rmdir()
```

**Sugestão:** Usar `shutil.rmtree(output_dir, ignore_errors=True)`.

---

## 3. Sugestões para Escalabilidade

### E1 — Extrair uma Classe Pipeline

Permitiria uso programático além do CLI:

```python
# pipeline.py
class ArgusPipeline:
    def __init__(self, collectors, processors, ai_enabled=False):
        self.collectors = collectors
        self.processors = processors
        self.ai_enabled = ai_enabled

    async def run(self, target, search_type):
        raw = await asyncio.gather(*[c.collect(target) for c in self.collectors])
        results = self._process(raw)
        return results
```

### E2 — Registry de Collectors

Para adicionar novos collectors sem modificar `argus.py`:

```python
# collectors/registry.py
COLLECTOR_REGISTRY = {
    "username": [MaigretCollector],
    "email": [HoleheCollector],
}

def get_collectors(search_type: str) -> List[Collector]:
    return [cls() for cls in COLLECTOR_REGISTRY.get(search_type, [])]
```

### E3 — Suporte a Plugins

Permitir collectors externos via entry points do setuptools:

```toml
# pyproject.toml
[project.entry-points."argus.collectors"]
sherlock = "argus_sherlock:SherlockCollector"
```

### E4 — Cache de Resultados

Para evitar re-execução de collectors lentos:

```python
# cache.py
import hashlib, json
from pathlib import Path

class ResultCache:
    def __init__(self, cache_dir=".argus_cache", ttl=3600):
        self.cache_dir = Path(cache_dir)
        self.ttl = ttl

    def get(self, key: str) -> Optional[List[dict]]:
        ...

    def set(self, key: str, results: List[dict]):
        ...
```

### E5 — Separar Modelos de Saída dos Modelos Internos

O `Enricher` retorna `List[Dict]` em vez de objetos tipados. Isso cria um contrato fraco entre processamento e output. Considerar criar um `EnrichedResult` dataclass.

### E6 — Logging Estruturado

Substituir `logging` básico por logging estruturado (ex: `structlog`) para facilitar observabilidade em produção.

---

## 4. Áreas que Seguem Boas Práticas

### BP1 — Separação de Responsabilidades Clara

Cada módulo tem um propósito bem definido. `collectors/` coleta, `processing/` transforma, `ai/` analisa, `output/` formata. É fácil entender onde cada funcionalidade reside.

### BP2 — Error Handling nos Collectors

Os collectors **nunca propagam exceções** — sempre retornam `AccountResult` com status de erro. Isso garante que falhas parciais não interrompam o pipeline inteiro (`argus.py` nunca precisa de try/catch para collectors).

### BP3 — Dataclasses Tipadas

Uso de `@dataclass` para `AccountResult` e `AIReport` em vez de dicts genéricos fornece type safety, documentação inline e facilita IDE support.

### BP4 — Lazy Initialization do Cliente OpenAI

O `ReportGenerator` só instancia o cliente quando `generate()` é chamado (`report_generator.py:17-23`). Evita custo de conexão quando IA não é solicitada.

### BP5 — Configuração Externalizada

Todas as configurações sensíveis e ajustáveis estão em variáveis de ambiente com defaults sensatos. O `.env.example` documenta as opções disponíveis.

### BP6 — Testes E2E com Mocking Adequado

O `conftest.py` fornece fixtures que substituem dependências externas (subprocess, HTTP, OpenAI API). Os testes validam o pipeline completo sem depender de serviços externos.

### BP7 — XSS Prevention no HTML

O `formatter.py` usa `html.escape()` consistentemente ao gerar HTML, prevenindo injeção de conteúdo malicioso nos relatórios.

### BP8 — Async para I/O-Bound Operations

Coleta e validação HTTP usam `asyncio` para paralelismo, o que é ideal para operações I/O-bound como chamadas de rede e subprocessos.

---

## Resumo

| Área | Nota | Comentário |
|------|------|------------|
| **Separação de Responsabilidades** | Boa | Módulos bem divididos por função |
| **Testabilidade** | Boa | Mocks adequados, boa cobertura E2E |
| **Manutenibilidade** | Média | Orquestração acoplada ao CLI dificulta evolução |
| **Escalabilidade** | Média | Falta abstração para adicionar novos collectors/outputs |
| **Type Safety** | Média | Dataclasses nos extremos, dicts no meio do pipeline |
| **Configuração** | Boa | Externalizada com defaults sensatos |
| **Segurança** | Boa | XSS mitigado, sanitização de input |

**Prioridades recomendadas:**
1. Extrair pipeline do `argus.py` (P1) — maior impacto em manutenibilidade
2. Unificar event loop async (P2) — correctness
3. Formalizar interface de Collectors (P3) — extensibilidade
4. Tipar a camada intermediária (E5) — type safety end-to-end
