import json
from typing import Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ai.models import AIReport


class ReportFormatter:
    @staticmethod
    def to_json(target: str, results: List[Dict], ai_report: Optional[AIReport] = None) -> str:
        platforms_found = sum(1 for item in results if item["status"] == "found")
        report = {
            "target": target,
            "platforms_found": platforms_found,
            "platforms": results,
            "ai_analysis": ai_report.__dict__ if ai_report else None,
        }
        return json.dumps(report, indent=2, ensure_ascii=False)

    @staticmethod
    def to_html(target: str, results: List[Dict], ai_report: Optional[AIReport] = None) -> str:
        platforms_found = sum(1 for item in results if item["status"] == "found")
        platform_cards = "\n".join(
            f"""
            <div class="platform-card">
                <h3>{item["site_name"]}</h3>
                <p>Status: {item["status"]}</p>
                <p>Categoria: {item["metadata"]["category"]}</p>
                <p>{item["metadata"]["description"]}</p>
                {f'<a href="{item["url"]}" target="_blank">{item["url"]}</a>' if item["url"] else ""}
            </div>
            """
            for item in results
        )

        ai_block = ""
        if ai_report:
            ai_block = f"""
            <section class="ai-section">
                <h2>Análise de IA</h2>
                <p><strong>{ai_report.profile_type}</strong></p>
                <p>{ai_report.summary}</p>
                <p><strong>Score:</strong> {ai_report.digital_footprint_score}/10</p>
                <ul>{"".join(f"<li>{item}</li>" for item in ai_report.insights)}</ul>
            </section>
            """

        return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <title>ARGUS: {target}</title>
  <style>
    body {{ font-family: Arial, sans-serif; background: #f5f7fb; margin: 0; padding: 24px; }}
    .container {{ max-width: 960px; margin: 0 auto; background: #fff; border-radius: 12px; padding: 24px; }}
    .platform-card {{ background: #f8fafc; border-left: 4px solid #2563eb; margin: 12px 0; padding: 16px; }}
    .ai-section {{ margin-top: 24px; background: #eff6ff; padding: 20px; border-radius: 10px; }}
  </style>
</head>
<body>
  <div class="container">
    <h1>ARGUS: {target}</h1>
    <h2>Plataformas encontradas: {platforms_found}</h2>
    {platform_cards or "<p>Nenhuma plataforma encontrada.</p>"}
    {ai_block}
  </div>
</body>
</html>"""

    @staticmethod
    def to_cli(target: str, results: List[Dict], ai_report: Optional[AIReport] = None) -> None:
        console = Console()
        console.print(f"\n[bold cyan]ARGUS: {target}[/bold cyan]\n")

        table = Table(title="Resultados")
        table.add_column("Site", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Categoria", style="magenta")

        for item in results:
            table.add_row(
                item["site_name"],
                item["status"],
                item["metadata"]["category"],
            )

        if results:
            console.print(table)
        else:
            console.print("[yellow]Nenhum resultado validado encontrado.[/yellow]")

        if ai_report:
            console.print(
                Panel(
                    f"[bold]{ai_report.profile_type}[/bold]\n{ai_report.summary}",
                    title="Análise por IA",
                )
            )
            console.print(f"[bold yellow]Score: {ai_report.digital_footprint_score}/10[/bold yellow]")
