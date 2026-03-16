# ARGUS — Guia de Implementação Técnica Detalhado

## Índice

1. [Setup Completo do Projeto](#1-setup-completo-do-projeto)
2. [Estrutura de Pastas](#2-estrutura-de-pastas)
3. [Tipos de Dados (Type Definitions)](#3-tipos-de-dados)
4. [Coleta Paralela em Detalhes](#4-coleta-paralela-em-detalhes)
5. [Pipeline de Processamento](#5-pipeline-de-processamento)
6. [Análise com IA](#6-análise-com-ia)
7. [Formatação de Output](#7-formatação-de-output)
8. [Tratamento de Erros](#8-tratamento-de-erros)

---

## 1. Setup Completo do Projeto

### requirements.txt

```
# Core
asyncio-contextmanager==1.0.0
python-dotenv==1.0.0

# Collectors
maigret==0.3.14
holehe==0.15.4
sherlock==0.14.2

# HTTP
aiohttp==3.9.1
requests==2.31.0

# AI
openai==1.3.0

# Output
rich==13.7.0
jinja2==3.1.2

# Database
sqlalchemy==2.0.23
sqlite3

# Testing
pytest==7.4.0
pytest-asyncio==0.21.0

# Development
black==23.11.0
pylint==3.0.0
mypy==1.7.1
```

### .env Configuration

```env
# OpenAI
OPENAI_API_KEY=sk-seu-api-key-aqui
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.3

# Diretórios
ARGUS_OUTPUT_DIR=./reports
ARGUS_LOG_LEVEL=INFO

# Coleta
COLLECTOR_TIMEOUT=15
COLLECTOR_RETRIES=2
COLLECTOR_DELAY_BETWEEN_REQUESTS=0.5

# Filtro
VALIDATE_URLS=true
VALIDATION_TIMEOUT=5
MAX_PARALLEL_VALIDATIONS=10

# Cache
USE_CACHE=true
CACHE_TTL_HOURS=24
```

### setup.py

```python
from setuptools import setup, find_packages

setup(
    name="argus-osint",
    version="1.0.0",
    description="OSINT Suite profissional com análise de IA",
    author="Gabriel Ramos",
    author_email="gabriel@example.com",
    packages=find_packages(),
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "argus=argus.cli:main",
        ],
    },
    install_requires=[
        "aiohttp>=3.9.0",
        "requests>=2.31.0",
        "openai>=1.3.0",
        "rich>=13.7.0",
        "python-dotenv>=1.0.0",
        "maigret>=0.3.14",
        "holehe>=0.15.4",
        "sherlock>=0.14.2",
    ],
)
```

---

## 2. Estrutura de Pastas

```
argus/
├── README.md
├── requirements.txt
├── setup.py
├── .env
├── .gitignore
├── argus.py                          # CLI entry point
│
├── argus/
│   ├── __init__.py
│   │
│   ├── cli.py                        # CLI com Click/Typer
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py              # Carregamento de env vars
│   │   ├── platforms_metadata.json  # Database de plataformas
│   │   └── logger.py                # Setup de logging
│   │
│   ├── collectors/
│   │   ├── __init__.py
│   │   ├── base.py                  # Tipos + classe base
│   │   ├── maigret.py               # Integração Maigret
│   │   ├── holehe.py                # Integração Holehe
│   │   ├── sherlock.py              # Integração Sherlock
│   │   ├── ghunt.py                 # Integração GHunt
│   │   └── registry.py              # Registry pattern
│   │
│   ├── processing/
│   │   ├── __init__.py
│   │   ├── normalizer.py            # Normalização de resultados
│   │   ├── filter.py                # Validação HTTP + anti-FP
│   │   ├── enricher.py              # Adição de metadados
│   │   ├── cache.py                 # Cache com SQLite
│   │   └── pipeline.py              # Orquestração
│   │
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── models.py                # Tipos AIReport, etc
│   │   ├── prompt_builder.py        # Construção de prompt
│   │   ├── report_generator.py      # Integração OpenAI
│   │   ├── jailbreak_detector.py   # Detecção de jailbreaks
│   │   └── confidence_scorer.py     # Scoring de confiança
│   │
│   ├── output/
│   │   ├── __init__.py
│   │   ├── formatter.py             # Formatação (CLI/JSON/HTML)
│   │   ├── templates/
│   │   │   ├── report.html          # Template HTML jinja2
│   │   │   ├── styles.css           # Estilos
│   │   │   └── components.html      # Componentes reutilizáveis
│   │   └── pdf_generator.py         # Geração de PDF
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py                # SQLAlchemy ORM
│   │   └── repository.py            # Data access layer
│   │
│   └── utils/
│       ├── __init__.py
│       ├── validators.py            # Validadores
│       ├── exceptions.py            # Exceções customizadas
│       └── decorators.py            # Decoradores úteis
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  # Fixtures pytest
│   ├── unit/
│   │   ├── test_normalizer.py
│   │   ├── test_filter.py
│   │   └── test_enricher.py
│   ├── integration/
│   │   └── test_pipeline.py
│   └── fixtures/
│       └── sample_data.json
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── INSTALLATION.md
│   ├── API.md
│   └── EXAMPLES.md
│
└── reports/                         # Output directory (gitignored)
    ├── target1_report.json
    └── target1_report.html
```

---

## 3. Tipos de Dados

### collectors/base.py

```python
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class CollectorType(Enum):
    """Tipos de coleta suportados"""
    USERNAME = "username"
    EMAIL = "email"
    HYBRID = "hybrid"

class CollectorStatus(Enum):
    """Status possíveis de um collector"""
    FOUND = "found"
    NOT_FOUND = "not_found"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"
    TIMEOUT = "timeout"

@dataclass
class AccountResult:
    """Resultado bruto de um collector"""
    site_name: str
    target: str                    # username ou email
    url: str
    status: CollectorStatus
    http_status: Optional[int] = None
    collector_name: str = ""
    error_message: Optional[str] = None
    raw_html: Optional[str] = None
    extra_data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=lambda: time.time())
    
    @property
    def is_found(self) -> bool:
        return self.status == CollectorStatus.FOUND

@dataclass
class UnifiedResult:
    """Resultado normalizado após Normalizer"""
    site_name: str
    url: str
    http_status: int
    is_found: bool
    raw_data: Dict[str, Any] = field(default_factory=dict)
    verification_method: str = "http_validation"
    confidence: float = 1.0  # 0.0-1.0

@dataclass
class EnrichedResult(UnifiedResult):
    """Resultado após Enricher"""
    category: str = "unknown"
    data_richness: str = "low"      # high/medium/low
    description: str = ""
    verified: bool = False
    platform_icon_url: Optional[str] = None
    api_endpoint: Optional[str] = None
```

### ai/models.py

```python
from dataclasses import dataclass
from typing import List

@dataclass
class AIReport:
    """Saída final da análise LLM"""
    profile_summary: str
    profile_type: str
    insights: List[str]
    risk_flags: List[str]
    tags: List[str]
    digital_footprint_score: int  # 0-10
    confidence: str  # "high", "medium", "low"
    additional_context: str = ""
    
    @property
    def risk_level(self) -> str:
        if self.digital_footprint_score >= 8:
            return "high"
        elif self.digital_footprint_score >= 5:
            return "medium"
        else:
            return "low"
```

---

## 4. Coleta Paralela em Detalhes

### collectors/__init__.py

```python
import asyncio
import logging
from typing import Dict, List
from .base import CollectorType
from .maigret import MaigetCollector
from .holehe import HoleheCollector
from .sherlock import SherlockCollector
from .ghunt import GHuntCollector

logger = logging.getLogger(__name__)

class CollectionOrchestrator:
    """Orquestrador de coleta paralela"""
    
    def __init__(self):
        self.collectors = {
            "maigret": MaigetCollector(timeout=15, retries=2),
            "holehe": HoleheCollector(timeout=15, retries=2),
            "sherlock": SherlockCollector(timeout=15, retries=2),
            "ghunt": GHuntCollector(timeout=15, retries=2),
        }
    
    async def collect(self, username: Optional[str] = None, email: Optional[str] = None) -> Dict[str, List]:
        """Executar todos os collectors em paralelo"""
        
        tasks = []
        collector_order = []
        
        if username:
            # Collectors que usam username
            tasks.append(self.collectors["maigret"].collect(username))
            collector_order.append("maigret")
            
            tasks.append(self.collectors["sherlock"].collect(username))
            collector_order.append("sherlock")
        
        if email:
            # Collectors que usam email
            tasks.append(self.collectors["holehe"].collect(email))
            collector_order.append("holehe")
            
            tasks.append(self.collectors["ghunt"].collect(email))
            collector_order.append("ghunt")
        
        logger.info(f"🚀 Iniciando {len(tasks)} collectors em paralelo...")
        start_time = time.time()
        
        # Aguardar todas as tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        elapsed = time.time() - start_time
        logger.info(f"✅ Coleta concluída em {elapsed:.2f}s")
        
        # Mapear resultados
        all_results = []
        for collector_name, result in zip(collector_order, results):
            if isinstance(result, Exception):
                logger.error(f"❌ {collector_name}: {result}")
                continue
            all_results.extend(result)
        
        return {
            "total_found": len(all_results),
            "results": all_results,
            "elapsed_seconds": elapsed
        }
```

---

## 5. Pipeline de Processamento

### processing/pipeline.py

```python
import logging
from typing import List
from .normalizer import ResultNormalizer, UnifiedResult
from .filter import URLValidator
from .enricher import ResultEnricher, EnrichedResult
from ..collectors.base import AccountResult

logger = logging.getLogger(__name__)

class ProcessingPipeline:
    """Pipeline sequencial de processamento"""
    
    def __init__(self):
        self.normalizer = ResultNormalizer()
        self.validator = URLValidator(timeout=5)
        self.enricher = ResultEnricher()
    
    async def process(self, raw_results: List[AccountResult]) -> List[EnrichedResult]:
        """Executar pipeline completo"""
        
        logger.info(f"📥 Input: {len(raw_results)} raw results")
        
        # Etapa 1: Normalização
        logger.info("🔄 Etapa 1/3: Normalizing...")
        normalized = self.normalizer.normalize(raw_results)
        logger.info(f"   → {len(normalized)} normalized results")
        
        # Etapa 2: Filtro HTTP + Anti-FP
        logger.info("🔄 Etapa 2/3: Filtering (HTTP validation)...")
        filtered = await self.validator.filter_results(normalized)
        logger.info(f"   → {len(filtered)} valid results (removed {len(normalized) - len(filtered)} FPs)")
        
        # Etapa 3: Enriquecimento
        logger.info("🔄 Etapa 3/3: Enriching with metadata...")
        enriched = self.enricher.enrich(filtered)
        logger.info(f"   → {len(enriched)} enriched results")
        
        return enriched
```

---

## 6. Análise com IA

### ai/prompt_builder.py

```python
from typing import List
from ..processing.enricher import EnrichedResult

class PromptBuilder:
    """Construir prompt otimizado para LLM"""
    
    SYSTEM_PROMPT = """Você é um especialista em análise de OSINT (Open Source Intelligence).
Sua tarefa é analisar o perfil digital de uma pessoa baseado em dados públicos coletados.
Seja preciso, objetivo e estruturado na resposta.
Sempre retorne um JSON válido."""
    
    @staticmethod
    def build(results: List[EnrichedResult], max_tokens: int = 2000) -> str:
        """Construir prompt com resultados agrupados por data_richness"""
        
        # Agrupar por richness
        high = [r for r in results if r.data_richness == 'high']
        medium = [r for r in results if r.data_richness == 'medium']
        low = [r for r in results if r.data_richness == 'low']
        
        # Priorizar high richness se exceder token limit
        if len(results) > 50:
            results = high + medium[:20]
        
        prompt_parts = [
            "Analise o perfil digital desta pessoa com base nos seguintes dados:\n\n"
        ]
        
        # SEÇÃO 1: High Richness
        if high:
            prompt_parts.append("## PLATAFORMAS PRINCIPAIS (Dados Detalhados)\n\n")
            for i, r in enumerate(high[:10], 1):  # Limitar a 10
                prompt_parts.append(
                    f"{i}. **{r.site_name}** ({r.category})\n"
                    f"   URL: {r.url}\n"
                    f"   {r.description}\n\n"
                )
        
        # SEÇÃO 2: Medium Richness
        if medium:
            prompt_parts.append("## PLATAFORMAS SECUNDÁRIAS\n\n")
            for r in medium[:10]:
                prompt_parts.append(f"- {r.site_name}: {r.description}\n")
            prompt_parts.append("\n")
        
        # SEÇÃO 3: Low Richness
        if low:
            prompt_parts.append("## OUTROS PERFIS\n\n")
            for r in low[:15]:
                prompt_parts.append(f"- {r.site_name}: {r.url}\n")
        
        # Instruções finais
        prompt_parts.append("""
Gere um relatório JSON estruturado com os campos:
{
    "profile_summary": "Resumo de 2-3 linhas descritivas",
    "profile_type": "Classificação (e.g., Developer, Content Creator, Business Professional)",
    "insights": ["Insight 1", "Insight 2", "Insight 3", "Insight 4", "Insight 5"],
    "risk_flags": ["Risk 1", "Risk 2", "Risk 3"],
    "tags": ["Tag1", "Tag2", "Tag3", "Tag4"],
    "digital_footprint_score": <0-10>,
    "confidence": "high|medium|low"
}

IMPORTANTE:
- Seja específico e factual
- Baseie-se apenas nos dados fornecidos
- Se não tiver informação suficiente, marque confidence como "low"
- Scores: 8-10 = presença online muito forte | 5-7 = presença normal | 0-4 = presença fraca
""")
        
        return "".join(prompt_parts)
```

---

## 7. Formatação de Output

### output/formatter.py

```python
import json
from pathlib import Path
from typing import List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from ..ai.models import AIReport
from ..processing.enricher import EnrichedResult

class OutputFormatter:
    """Formatar output em múltiplos formatos"""
    
    def __init__(self, output_dir: str = "./reports"):
        self.console = Console()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def format_cli(self, target: str, results: List[EnrichedResult], report: AIReport) -> None:
        """Exibir como tabela Rich para CLI"""
        
        # Tabela de plataformas
        table = Table(title=f"🔍 ARGUS Report: {target}", show_header=True)
        table.add_column("Site", style="cyan", width=20)
        table.add_column("URL", style="green")
        table.add_column("Categoria", style="yellow")
        table.add_column("Richness", style="blue")
        
        for r in sorted(results, key=lambda x: x.data_richness, reverse=True):
            table.add_row(r.site_name, r.url[:40], r.category, r.data_richness.upper())
        
        self.console.print(table)
        
        # Análise de IA
        ai_content = f"""
[bold cyan]📊 ANÁLISE DE IA[/bold cyan]

{report.profile_summary}

[bold]Tipo de Perfil:[/bold] {report.profile_type}
[bold]Score:[/bold] {report.digital_footprint_score}/10
[bold]Confiança:[/bold] {report.confidence.upper()}

[bold green]✅ Insights:[/bold green]
"""
        for insight in report.insights:
            ai_content += f"  • {insight}\n"
        
        ai_content += f"\n[bold red]⚠️  Risk Flags:[/bold red]\n"
        for flag in report.risk_flags:
            ai_content += f"  • {flag}\n"
        
        ai_content += f"\n[bold]Tags:[/bold] {', '.join(report.tags)}"
        
        self.console.print(Panel(ai_content, title="AI Analysis"))
    
    def format_json(self, target: str, results: List[EnrichedResult], report: AIReport) -> str:
        """Formatar como JSON estruturado"""
        
        output = {
            "target": target,
            "metadata": {
                "platforms_found": len(results),
                "high_richness": len([r for r in results if r.data_richness == 'high']),
                "medium_richness": len([r for r in results if r.data_richness == 'medium']),
                "low_richness": len([r for r in results if r.data_richness == 'low']),
                "timestamp": datetime.now().isoformat()
            },
            "platforms": [
                {
                    "site_name": r.site_name,
                    "url": r.url,
                    "category": r.category,
                    "data_richness": r.data_richness,
                    "description": r.description,
                    "verified": r.verified,
                    "confidence": r.confidence
                }
                for r in results
            ],
            "ai_analysis": {
                "profile_summary": report.profile_summary,
                "profile_type": report.profile_type,
                "insights": report.insights,
                "risk_flags": report.risk_flags,
                "tags": report.tags,
                "digital_footprint_score": report.digital_footprint_score,
                "confidence": report.confidence,
                "risk_level": report.risk_level
            }
        }
        
        return json.dumps(output, indent=2, ensure_ascii=False)
    
    def save_reports(self, target: str, json_content: str, html_content: str) -> None:
        """Salvar reports em arquivo"""
        
        json_file = self.output_dir / f"{target}_report.json"
        html_file = self.output_dir / f"{target}_report.html"
        
        json_file.write_text(json_content, encoding='utf-8')
        html_file.write_text(html_content, encoding='utf-8')
        
        self.console.print(f"\n✅ Reports salvos:")
        self.console.print(f"   JSON: {json_file}")
        self.console.print(f"   HTML: {html_file}")
```

---

## 8. Tratamento de Erros

### utils/exceptions.py

```python
class ARGUSException(Exception):
    """Exceção base do ARGUS"""
    pass

class CollectorError(ARGUSException):
    """Erro durante coleta"""
    pass

class ValidationError(ARGUSException):
    """Erro durante validação"""
    pass

class EnrichmentError(ARGUSException):
    """Erro durante enriquecimento"""
    pass

class AIAnalysisError(ARGUSException):
    """Erro durante análise com IA"""
    pass

class FormattingError(ARGUSException):
    """Erro durante formatação de output"""
    pass

class RateLimitError(ARGUSException):
    """Rate limiting atingido"""
    pass
```

### config/logger.py

```python
import logging
import logging.handlers
from pathlib import Path

def setup_logging(log_level: str = "INFO", log_dir: str = "./logs") -> None:
    """Setup logging estruturado"""
    
    Path(log_dir).mkdir(exist_ok=True)
    
    # Handler para arquivo
    file_handler = logging.handlers.RotatingFileHandler(
        f"{log_dir}/argus.log",
        maxBytes=10_000_000,
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level))
    console_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
```

---

**Documentação técnica mantida por:** Gabriel Ramos (@ASOF)  
**Última atualização:** 16/03/2026  
**Status:** Production Ready v1.0