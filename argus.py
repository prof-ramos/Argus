import asyncio
import webbrowser
from typing import Optional

import typer
from rich.console import Console

from collectors.maigret import MaigreCollector
from collectors.holehe import HoleheCollector
from processing.normalizer import Normalizer
from processing.filter import FalsePositiveFilter
from processing.enricher import Enricher
from ai.report_generator import ReportGenerator
from output.formatter import ReportFormatter
from config.settings import OPENAI_API_KEY, OUTPUT_DIR

console = Console()
app = typer.Typer(help="ARGUS — OSINT Suite com IA", rich_markup_mode="rich")


@app.command()
def search(
    username: Optional[str] = typer.Option(None, "--username", "-u", help="Username"),
    email: Optional[str] = typer.Option(None, "--email", "-e", help="Email"),
    ai: bool = typer.Option(False, "--ai", help="Análise com IA"),
    output_format: str = typer.Option("cli", "--format", "-f", help="Formato: cli, json, html"),
    open_browser: bool = typer.Option(False, "--open", help="Abrir HTML no browser"),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="OpenAI API Key")
):
    """Busca e analisa presença online."""

    if not username and not email:
        console.print("[red]Especifique --username ou --email[/red]")
        raise typer.Exit(1)

    if ai and not (api_key or OPENAI_API_KEY):
        console.print("[red]IA requer OpenAI API Key (--api-key ou variável OPENAI_API_KEY)[/red]")
        raise typer.Exit(1)

    # Coleta
    with console.status("[bold cyan]Coletando..."):
        async def collect():
            tasks = []
            if username:
                tasks.append(MaigreCollector().collect(username))
            if email:
                tasks.append(HoleheCollector().collect(email))
            return await asyncio.gather(*tasks)

        all_results = asyncio.run(collect())

    # Processamento
    with console.status("[bold cyan]Processando..."):
        normalized = Normalizer.normalize(all_results)
        filtered = asyncio.run(FalsePositiveFilter().filter(normalized))
        enriched = Enricher().enrich(filtered)

    # IA
    ai_report = None
    if ai:
        with console.status("[bold cyan]Analisando com IA..."):
            gen = ReportGenerator(api_key=api_key)
            ai_report = gen.generate(
                username or email,
                enriched,
                "username" if username else "email"
            )

    # Output
    formatter = ReportFormatter()

    if output_format == "json":
        output = formatter.to_json(username or email, enriched, ai_report)
        print(output)
        output_file = OUTPUT_DIR / f"{username or email}_report.json"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output)
        console.print(f"[green]Salvo: {output_file}[/green]")

    elif output_format == "html":
        output = formatter.to_html(username or email, enriched, ai_report)
        output_file = OUTPUT_DIR / f"{username or email}_report.html"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output)
        console.print(f"[green]Salvo: {output_file}[/green]")
        if open_browser:
            import webbrowser
            webbrowser.open(output_file.as_uri())

    else:
        formatter.to_cli(username or email, enriched, ai_report)


@app.command()
def version():
    """Exibe a versão do ARGUS."""
    console.print("[bold cyan]ARGUS 1.0.0[/bold cyan]")


if __name__ == "__main__":
    app()
