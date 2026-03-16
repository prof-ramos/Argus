import asyncio
import webbrowser
from typing import Optional

import typer
from rich.console import Console

from ai.report_generator import ReportGenerator
from collectors.holehe import HoleheCollector
from collectors.maigret import MaigreCollector
from config.settings import OPENAI_API_KEY, OUTPUT_DIR
from output.formatter import ReportFormatter
from processing.enricher import Enricher
from processing.filter import FalsePositiveFilter
from processing.normalizer import Normalizer

console = Console()
app = typer.Typer(help="ARGUS - OSINT Suite com IA", rich_markup_mode="rich")


async def _collect(username: Optional[str], email: Optional[str]):
    tasks = []
    collectors_run = 0
    if username:
        tasks.append(MaigreCollector().collect(username))
        collectors_run += 1
    if email:
        tasks.append(HoleheCollector().collect(email))
        collectors_run += 1
    return collectors_run, await asyncio.gather(*tasks)


def _target_label(username: Optional[str], email: Optional[str]) -> str:
    return username or email or "unknown"


@app.command()
def search(
    username: Optional[str] = typer.Option(None, "--username", "-u", help="Username alvo"),
    email: Optional[str] = typer.Option(None, "--email", "-e", help="Email alvo"),
    ai: bool = typer.Option(False, "--ai", help="Executa analise com OpenAI"),
    output_format: str = typer.Option("cli", "--format", "-f", help="cli, json ou html"),
    open_browser: bool = typer.Option(False, "--open", help="Abre relatorio HTML"),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="OpenAI API Key para uso inline"),
):
    """Busca e analisa presenca online."""
    if not username and not email:
        console.print("[red]Especifique --username ou --email.[/red]")
        raise typer.Exit(code=1)

    if ai and not (api_key or OPENAI_API_KEY):
        console.print("[red]OPENAI_API_KEY nao configurada para --ai.[/red]")
        raise typer.Exit(code=1)

    target = _target_label(username, email)

    with console.status("[bold cyan]Coletando dados..."):
        collectors_run, all_results = asyncio.run(_collect(username, email))

    with console.status("[bold cyan]Processando resultados..."):
        normalized = Normalizer.normalize(all_results)
        summary = Normalizer.summarize(normalized)
        filtered = asyncio.run(FalsePositiveFilter().filter(normalized))
        enriched = Enricher().enrich(filtered)
        valid_found = sum(1 for item in enriched if item["status"] == "found")

    console.print(
        f"[cyan]Coletores executados:[/cyan] {collectors_run} | "
        f"[yellow]falhas:[/yellow] {summary['collector_failures']} | "
        f"[green]plataformas validas:[/green] {valid_found}"
    )

    ai_report = None
    if ai:
        with console.status("[bold cyan]Gerando analise por IA..."):
            ai_report = ReportGenerator(api_key=api_key).generate(
                target,
                enriched,
                "username" if username else "email",
            )

    formatter = ReportFormatter()
    if output_format == "json":
        output = formatter.to_json(target, enriched, ai_report)
        output_file = OUTPUT_DIR / f"{target}_report.json"
        output_file.write_text(output)
        console.print(f"[green]Relatorio salvo em {output_file}[/green]")
        print(output)
        return

    if output_format == "html":
        output = formatter.to_html(target, enriched, ai_report)
        output_file = OUTPUT_DIR / f"{target}_report.html"
        output_file.write_text(output)
        console.print(f"[green]Relatorio salvo em {output_file}[/green]")
        if open_browser:
            webbrowser.open(output_file.resolve().as_uri())
        return

    formatter.to_cli(target, enriched, ai_report)


@app.command()
def version() -> None:
    """Mostra a versao da CLI."""
    console.print("[bold cyan]ARGUS 1.0.0[/bold cyan]")


if __name__ == "__main__":
    app()
