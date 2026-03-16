# ARGUS — Código Completo Pronto para Usar

## Instruções de Deploy

1. Crie a pasta: `mkdir argus && cd argus`
2. Crie os arquivos abaixo com os nomes e conteúdo exatos
3. Execute: `pip install -e .`
4. Configure `.env` com sua OpenAI API Key
5. Teste: `argus --username seu-usuario`

---

## requirements.txt

```txt
requests==2.31.0
aiohttp==3.9.1
httpx==0.25.0
click==8.1.7
rich==13.7.0
typer==0.9.0
openai==1.3.0
pydantic==2.5.0
python-dotenv==1.0.0
tqdm==4.66.1
colorama==0.4.6
maigret==0.3.7
holehe==1.0.1
```

---

## setup.py

```python
from setuptools import setup, find_packages

setup(
    name="argus-osint",
    version="1.0.0",
    author="Gabriel Ramos",
    description="OSINT Suite com análise por IA",
    packages=find_packages(),
    install_requires=open("requirements.txt").read().splitlines(),
    entry_points={
        "console_scripts": [
            "argus=argus:app",
        ],
    },
    python_requires=">=3.10",
)
```

---

## config/__init__.py

```python
# Config package
```

---

## config/settings.py

```python
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = Path(os.getenv("ARGUS_OUTPUT_DIR", "./reports"))
OUTPUT_DIR.mkdir(exist_ok=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", 0.3))

COLLECTOR_TIMEOUT = int(os.getenv("COLLECTOR_TIMEOUT", 15))
COLLECTOR_RETRIES = int(os.getenv("COLLECTOR_RETRIES", 2))

VALIDATE_URLS = os.getenv("VALIDATE_URLS", "true").lower() == "true"
VALIDATION_TIMEOUT = int(os.getenv("VALIDATION_TIMEOUT", 5))

LOG_LEVEL = os.getenv("ARGUS_LOG_LEVEL", "INFO")

FALSE_POSITIVE_SITES = [
    "example.com",
    "test.com",
]
```

---

## config/platforms_metadata.json

```json
{
  "platforms": {
    "github": {
      "name": "GitHub",
      "category": "developer",
      "data_richness": "high",
      "description": "Repositórios, bio, followers, contribuições"
    },
    "twitter": {
      "name": "Twitter/X",
      "category": "social",
      "data_richness": "high",
      "description": "Tweets públicos, seguidores, localização"
    },
    "reddit": {
      "name": "Reddit",
      "category": "social",
      "data_richness": "high",
      "description": "Posts, comentários, histórico"
    },
    "linkedin": {
      "name": "LinkedIn",
      "category": "professional",
      "data_richness": "high",
      "description": "Experiência profissional, educação"
    },
    "twitch": {
      "name": "Twitch",
      "category": "streaming",
      "data_richness": "high",
      "description": "Canais, seguidores, streams"
    },
    "youtube": {
      "name": "YouTube",
      "category": "streaming",
      "data_richness": "high",
      "description": "Canais, vídeos, inscritos"
    },
    "duolingo": {
      "name": "Duolingo",
      "category": "education",
      "data_richness": "low",
      "description": "Idiomas estudados, streak"
    },
    "chess.com": {
      "name": "Chess.com",
      "category": "gaming",
      "data_richness": "medium",
      "description": "Rating, histórico, estatísticas"
    },
    "spotify": {
      "name": "Spotify",
      "category": "entertainment",
      "data_richness": "medium",
      "description": "Gosto musical, playlists"
    },
    "wordpress": {
      "name": "WordPress",
      "category": "blogging",
      "data_richness": "medium",
      "description": "Blog, posts públicos"
    }
  }
}
```

---

## collectors/__init__.py

```python
from .base import AccountResult, ResultStatus
from .maigret import MaigreCollector
from .holehe import HoleheCollector

__all__ = ["AccountResult", "ResultStatus", "MaigreCollector", "HoleheCollector"]
```

---

## collectors/base.py

```python
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

class ResultStatus(Enum):
    FOUND = "found"
    NOT_FOUND = "not_found"
    ERROR = "error"
    TIMEOUT = "timeout"

@dataclass
class AccountResult:
    site_name: str
    url: Optional[str] = None
    status: ResultStatus = ResultStatus.NOT_FOUND
    http_status: Optional[int] = None
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def is_valid(self) -> bool:
        return self.status == ResultStatus.FOUND and self.http_status == 200
```

---

## collectors/maigret.py

```python
import subprocess
import json
import asyncio
from typing import List
from .base import AccountResult, ResultStatus
from config.settings import COLLECTOR_TIMEOUT

class MaigreCollector:
    def __init__(self):
        self.name = "Maigret"

    async def collect(self, username: str) -> List[AccountResult]:
        try:
            result = await asyncio.wait_for(
                self._run_maigret(username),
                timeout=COLLECTOR_TIMEOUT
            )
            return self._parse_results(result)
        except asyncio.TimeoutError:
            return [AccountResult(
                site_name="Maigret",
                status=ResultStatus.TIMEOUT,
                error="Timeout"
            )]
        except Exception as e:
            return [AccountResult(
                site_name="Maigret",
                status=ResultStatus.ERROR,
                error=str(e)
            )]

    async def _run_maigret(self, username: str) -> dict:
        output_file = f"/tmp/maigret_{username}.json"

        proc = await asyncio.create_subprocess_exec(
            "maigret", username, "--json", "--output", output_file,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        await proc.communicate()

        try:
            with open(output_file) as f:
                return json.load(f)
        except:
            return {"results": {}}

    def _parse_results(self, maigret_output: dict) -> List[AccountResult]:
        results = []

        for username_data in maigret_output.get("results", {}).values():
            for site_name, site_data in username_data.items():
                if isinstance(site_data, dict):
                    status = ResultStatus.FOUND if site_data.get("found") else ResultStatus.NOT_FOUND
                    results.append(AccountResult(
                        site_name=site_name,
                        url=site_data.get("url"),
                        status=status,
                        http_status=site_data.get("status_code"),
                        metadata=site_data
                    ))

        return results
```

---

## collectors/holehe.py

```python
import subprocess
import asyncio
import re
from typing import List
from .base import AccountResult, ResultStatus
from config.settings import COLLECTOR_TIMEOUT

class HoleheCollector:
    def __init__(self):
        self.name = "Holehe"

    async def collect(self, email: str) -> List[AccountResult]:
        try:
            result = await asyncio.wait_for(
                self._run_holehe(email),
                timeout=COLLECTOR_TIMEOUT
            )
            return self._parse_results(result, email)
        except asyncio.TimeoutError:
            return [AccountResult(
                site_name="Holehe",
                status=ResultStatus.TIMEOUT,
                error="Timeout"
            )]
        except Exception as e:
            return [AccountResult(
                site_name="Holehe",
                status=ResultStatus.ERROR,
                error=str(e)
            )]

    async def _run_holehe(self, email: str) -> str:
        proc = await asyncio.create_subprocess_exec(
            "holehe", email, "--only-used", "--no-color",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, _ = await proc.communicate()
        return stdout.decode('utf-8', errors='ignore')

    def _parse_results(self, output: str, email: str) -> List[AccountResult]:
        results = []
        pattern = r"(.+?)\s*:\s*(found|not found)"
        matches = re.findall(pattern, output, re.IGNORECASE)

        for site_name, status in matches:
            results.append(AccountResult(
                site_name=site_name.strip(),
                status=ResultStatus.FOUND if status.lower() == "found" else ResultStatus.NOT_FOUND,
                http_status=200 if status.lower() == "found" else 404
            ))

        return results
```

---

## processing/__init__.py

```python
from .normalizer import Normalizer
from .filter import FalsePositiveFilter
from .enricher import Enricher

__all__ = ["Normalizer", "FalsePositiveFilter", "Enricher"]
```

---

## processing/normalizer.py

```python
from typing import List
from collectors.base import AccountResult

class Normalizer:
    @staticmethod
    def normalize(all_results: List[List[AccountResult]]) -> List[AccountResult]:
        flattened = []

        for results in all_results:
            flattened.extend(results)

        seen = set()
        normalized = []

        for result in flattened:
            key = (result.site_name, result.url)
            if key not in seen and result.url:
                seen.add(key)
                normalized.append(result)

        return normalized
```

---

## processing/filter.py

```python
import asyncio
import aiohttp
from typing import List
from collectors.base import AccountResult, ResultStatus
from config.settings import VALIDATE_URLS, VALIDATION_TIMEOUT, FALSE_POSITIVE_SITES

class FalsePositiveFilter:
    def __init__(self):
        self.blocklist = FALSE_POSITIVE_SITES

    async def filter(self, results: List[AccountResult]) -> List[AccountResult]:
        if not VALIDATE_URLS:
            return results

        tasks = [self._validate_single(r) for r in results]
        validated = await asyncio.gather(*tasks)

        return [r for r in validated if r is not None]

    async def _validate_single(self, result: AccountResult):
        if result.status != ResultStatus.FOUND or not result.url:
            return result

        if any(fp in result.url for fp in self.blocklist):
            return None

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    result.url,
                    timeout=aiohttp.ClientTimeout(total=VALIDATION_TIMEOUT),
                    allow_redirects=True
                ) as resp:
                    if resp.url != result.url and "404" not in str(resp.url):
                        return None

                    if resp.status == 200:
                        result.http_status = 200
                        return result
                    else:
                        return None
        except:
            return None
```

---

## processing/enricher.py

```python
import json
from pathlib import Path
from typing import List, Dict
from collectors.base import AccountResult
from config.settings import BASE_DIR

class Enricher:
    def __init__(self):
        metadata_path = BASE_DIR / "config" / "platforms_metadata.json"
        with open(metadata_path) as f:
            self.platform_data = json.load(f)["platforms"]

    def enrich(self, results: List[AccountResult]) -> List[Dict]:
        enriched = []

        for result in results:
            site_key = result.site_name.lower().replace(" ", "-").replace(".", "")
            platform_meta = self.platform_data.get(site_key, {})

            enriched.append({
                "site_name": result.site_name,
                "url": result.url,
                "status": result.status.value,
                "http_status": result.http_status,
                "metadata": {
                    **result.metadata,
                    "category": platform_meta.get("category", "unknown"),
                    "data_richness": platform_meta.get("data_richness", "low"),
                    "description": platform_meta.get("description", "")
                }
            })

        return enriched
```

---

## ai/__init__.py

```python
from .models import AIReport
from .prompt_builder import PromptBuilder
from .report_generator import ReportGenerator

__all__ = ["AIReport", "PromptBuilder", "ReportGenerator"]
```

---

## ai/models.py

```python
from dataclasses import dataclass
from typing import List

@dataclass
class AIReport:
    summary: str
    profile_type: str
    insights: List[str]
    risk_flags: List[str]
    tags: List[str]
    digital_footprint_score: int
    confidence: str
    platforms_found: int
    high_value_platforms: List[str]
    categories: List[str]
```

---

## ai/prompt_builder.py

```python
from typing import List, Dict

class PromptBuilder:
    @staticmethod
    def build(username: str, results: List[Dict], search_type: str = "username") -> str:
        platforms = [r["site_name"] for r in results]
        categories = list(set(r["metadata"]["category"] for r in results))
        high_value = [r["site_name"] for r in results
                      if r["metadata"]["data_richness"] == "high"]

        return f"""You are an OSINT analyst specializing in behavioral profiling.

Based SOLELY on the list of platforms where a target was found, generate a structured intelligence report.

Target: {username}
Search Type: {search_type}
Platforms Confirmed ({len(platforms)} total): {", ".join(platforms)}
High-Value Platforms: {", ".join(high_value) if high_value else "none"}
Categories Represented: {", ".join(categories)}

Your analysis must be based strictly on known user demographics and behaviors associated with each platform.
Do NOT invent facts or make unfounded claims.

Generate output as valid JSON with exactly these fields:
{{
  "summary": "2-3 sentence narrative profile",
  "profile_type": "Single descriptive label",
  "insights": ["insight 1", "insight 2"],
  "risk_flags": ["flag 1", "flag 2"],
  "tags": ["tag1", "tag2"],
  "digital_footprint_score": 5,
  "confidence": "medium"
}}

Respond in Portuguese (Brazil). Return ONLY valid JSON."""
```

---

## ai/report_generator.py

```python
import json
from typing import Optional
from openai import OpenAI
from ai.models import AIReport
from ai.prompt_builder import PromptBuilder
from config.settings import OPENAI_API_KEY, LLM_MODEL, LLM_TEMPERATURE

class ReportGenerator:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = LLM_MODEL

    def generate(self, username: str, results: list, search_type: str = "username") -> Optional[AIReport]:
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not configured")

        prompt = PromptBuilder.build(username, results, search_type)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=LLM_TEMPERATURE,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            report_data = json.loads(content)

            return AIReport(
                summary=report_data.get("summary", ""),
                profile_type=report_data.get("profile_type", "Unknown"),
                insights=report_data.get("insights", []),
                risk_flags=report_data.get("risk_flags", []),
                tags=report_data.get("tags", []),
                digital_footprint_score=report_data.get("digital_footprint_score", 5),
                confidence=report_data.get("confidence", "low"),
                platforms_found=len(results),
                high_value_platforms=[r["site_name"] for r in results
                                     if r["metadata"]["data_richness"] == "high"],
                categories=list(set(r["metadata"]["category"] for r in results))
            )

        except Exception as e:
            print(f"❌ Erro: {e}")
            return None
```

---

## output/__init__.py

```python
from .formatter import ReportFormatter

__all__ = ["ReportFormatter"]
```

---

## output/formatter.py

```python
import json
from typing import List, Dict
from ai.models import AIReport
from config.settings import OUTPUT_DIR

class ReportFormatter:
    @staticmethod
    def to_json(username: str, results: List[Dict], ai_report: AIReport = None) -> str:
        report = {
            "target": username,
            "platforms_found": len(results),
            "platforms": results,
            "ai_analysis": ai_report.__dict__ if ai_report else None
        }
        return json.dumps(report, indent=2, ensure_ascii=False)

    @staticmethod
    def to_html(username: str, results: List[Dict], ai_report: AIReport = None) -> str:
        platforms_html = "\n".join([
            f"""
            <div class="platform-card">
                <h3>{r['site_name']}</h3>
                <a href="{r['url']}" target="_blank">{r['url']}</a>
                <span class="category">{r['metadata']['category']}</span>
            </div>
            """ for r in results
        ])

        insights_html = ""
        if ai_report:
            insights_html = f"""
            <section class="ai-section">
                <h2>Análise de IA</h2>
                <div class="summary">{ai_report.summary}</div>
                <h3>{ai_report.profile_type}</h3>
                <div class="score">Score: {ai_report.digital_footprint_score}/10</div>
                <div class="insights">
                    <h4>Insights:</h4>
                    <ul>{"".join([f"<li>{i}</li>" for i in ai_report.insights])}</ul>
                </div>
                <div class="risks">
                    <h4>Risk Flags:</h4>
                    <ul>{"".join([f"<li>{f}</li>" for f in ai_report.risk_flags])}</ul>
                </div>
                <div class="tags"><strong>Tags:</strong> {", ".join(ai_report.tags)}</div>
            </section>
            """

        html = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <title>ARGUS: {username}</title>
            <style>
                body {{ font-family: -apple-system, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
                .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; }}
                h1 {{ color: #1a1a2e; border-bottom: 3px solid #4a90d9; padding-bottom: 10px; }}
                .platform-card {{ background: #f9f9f9; padding: 15px; margin: 10px 0; border-left: 4px solid #4a90d9; }}
                .platform-card a {{ color: #4a90d9; text-decoration: none; }}
                .platform-card .category {{ display: inline-block; background: #e0f0ff; color: #0066cc; padding: 2px 8px; margin-left: 10px; font-size: 12px; }}
                .ai-section {{ background: #f0f8ff; padding: 20px; margin-top: 30px; border-radius: 8px; }}
                .score {{ font-size: 18px; font-weight: bold; color: #4a90d9; margin: 15px 0; }}
                .risks {{ color: #e74c3c; margin-top: 15px; }}
                .tags {{ margin-top: 15px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔍 ARGUS: {username}</h1>
                <div class="platforms"><h2>Plataformas ({len(results)})</h2>{platforms_html}</div>
                {insights_html}
            </div>
        </body>
        </html>
        """
        return html

    @staticmethod
    def to_cli(username: str, results: List[Dict], ai_report: AIReport = None):
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel

        console = Console()
        console.print(f"\n[bold cyan]🔍 ARGUS: {username}[/bold cyan]\n")

        table = Table(title="Plataformas Encontradas")
        table.add_column("Site", style="cyan")
        table.add_column("Categoria", style="magenta")

        for r in results:
            table.add_row(r["site_name"], r["metadata"]["category"])

        console.print(table)

        if ai_report:
            console.print(Panel(
                f"[bold]{ai_report.profile_type}[/bold]\n{ai_report.summary}",
                title="📊 Análise"
            ))
            console.print(f"\n[bold yellow]Score: {ai_report.digital_footprint_score}/10[/bold yellow]")
```

---

## argus.py (ARQUIVO PRINCIPAL)

```python
import asyncio
import typer
from typing import Optional
from rich.console import Console
import json
from pathlib import Path

from collectors.maigret import MaigreCollector
from collectors.holehe import HoleheCollector
from processing.normalizer import Normalizer
from processing.filter import FalsePositiveFilter
from processing.enricher import Enricher
from ai.report_generator import ReportGenerator
from output.formatter import ReportFormatter
from config.settings import OPENAI_API_KEY, OUTPUT_DIR

console = Console()
app = typer.Typer(help="🔍 ARGUS — OSINT Suite com IA", rich_markup_mode="rich")

@app.command()
def search(
    username: Optional[str] = typer.Option(None, "--username", "-u", help="Username"),
    email: Optional[str] = typer.Option(None, "--email", "-e", help="Email"),
    ai: bool = typer.Option(False, "--ai", help="Análise com IA"),
    format: str = typer.Option("cli", "--format", "-f", help="Formato: cli, json, html"),
    open_browser: bool = typer.Option(False, "--open", help="Abrir HTML"),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="OpenAI API Key")
):
    """Busca e analisa presença online"""

    if not username and not email:
        console.print("[red]❌ Especifique --username ou --email[/red]")
        raise typer.Exit(1)

    if ai and not (api_key or OPENAI_API_KEY):
        console.print("[red]❌ IA requer OpenAI API Key[/red]")
        raise typer.Exit(1)

    # Coleta
    with console.status("[bold cyan]⚙️ Coletando..."):
        async def collect():
            tasks = []
            if username:
                tasks.append(MaigreCollector().collect(username))
            if email:
                tasks.append(HoleheCollector().collect(email))
            return await asyncio.gather(*tasks)

        all_results = asyncio.run(collect())

    # Processamento
    with console.status("[bold cyan]🔬 Processando..."):
        normalized = Normalizer.normalize(all_results)
        filtered = asyncio.run(FalsePositiveFilter().filter(normalized))
        enriched = Enricher().enrich(filtered)

    # IA
    ai_report = None
    if ai:
        with console.status("[bold cyan]🤖 Analisando..."):
            gen = ReportGenerator()
            ai_report = gen.generate(username or email, enriched, "username" if username else "email")

    # Output
    formatter = ReportFormatter()

    if format == "json":
        output = formatter.to_json(username or email, enriched, ai_report)
        print(output)
        output_file = OUTPUT_DIR / f"{username or email}_report.json"
        with open(output_file, "w") as f:
            f.write(output)
        console.print(f"[green]✅ Salvo: {output_file}[/green]")

    elif format == "html":
        output = formatter.to_html(username or email, enriched, ai_report)
        output_file = OUTPUT_DIR / f"{username or email}_report.html"
        with open(output_file, "w") as f:
            f.write(output)
        console.print(f"[green]✅ Salvo: {output_file}[/green]")
        if open_browser:
            import webbrowser
            webbrowser.open(output_file.as_uri())

    else:
        formatter.to_cli(username or email, enriched, ai_report)

@app.command()
def version():
    """Versão"""
    console.print("[bold cyan]ARGUS 1.0.0[/bold cyan]")

if __name__ == "__main__":
    app()
```

---

## .env (EXEMPLO)

```env
OPENAI_API_KEY=sk-seu-api-key-aqui
ARGUS_OUTPUT_DIR=./reports
ARGUS_LOG_LEVEL=INFO
COLLECTOR_TIMEOUT=15
VALIDATE_URLS=true
```

---

## README.md

```markdown
# 🔍 ARGUS — OSINT Suite com IA

OSINT Suite profissional com coleta paralela, validação HTTP e análise comportamental via IA.

## Setup Rápido

```bash
git clone seu-repo argus
cd argus
pip install -e .

echo "OPENAI_API_KEY=sk-..." > .env
```

## Uso

```bash
# Busca simples
argus --username johndoe

# Com IA
argus --username johndoe --ai --format html --open

# Por email
argus --email john@example.com --ai

# JSON
argus --username johndoe --format json
```

## Features

- ✅ Coleta paralela: Maigret + Holehe
- ✅ Filtro anti-falso-positivo (validação HTTP real)
- ✅ Enriquecimento com metadados de plataformas
- ✅ Análise com GPT-4o-mini
- ✅ Output: CLI, JSON, HTML

Criado com ❤️ para investigação responsável.
```

---

## Estrutura Final

```
argus/
├── argus.py
├── requirements.txt
├── setup.py
├── README.md
├── .env
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── platforms_metadata.json
├── collectors/
│   ├── __init__.py
│   ├── base.py
│   ├── maigret.py
│   └── holehe.py
├── processing/
│   ├── __init__.py
│   ├── normalizer.py
│   ├── filter.py
│   └── enricher.py
├── ai/
│   ├── __init__.py
│   ├── models.py
│   ├── prompt_builder.py
│   └── report_generator.py
└── output/
    ├── __init__.py
    └── formatter.py
```

## Deploy

```bash
# 1. Clone/Crie os arquivos acima
# 2. pip install -e .
# 3. Edite .env com sua OpenAI API Key
# 4. argus --username seu-usuario --ai
```
