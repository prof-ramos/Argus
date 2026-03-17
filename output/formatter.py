import json
import html as html_lib
from typing import List, Dict, Optional
from ai.models import AIReport


class ReportFormatter:
    @staticmethod
    def to_json(target: str, results: List[Dict], ai_report: Optional[AIReport] = None) -> str:
        report = {
            "target": target,
            "platforms_found": len(results),
            "platforms": results,
            "ai_analysis": ai_report.__dict__ if ai_report else None
        }
        return json.dumps(report, indent=2, ensure_ascii=False)

    @staticmethod
    def to_html(target: str, results: List[Dict], ai_report: Optional[AIReport] = None) -> str:
        safe_target = html_lib.escape(target)

        platforms_html = "\n".join([
            f"""
            <div class="platform-card">
                <h3>{html_lib.escape(r['site_name'])}</h3>
                {'<a href="' + html_lib.escape(r['url']) + '" target="_blank" rel="noopener noreferrer">' + html_lib.escape(r['url']) + '</a>' if r.get('url') else '<span>N/A</span>'}
                <span class="category">{html_lib.escape(r.get('metadata', {}).get('category', 'unknown'))}</span>
            </div>
            """ for r in results
        ])

        insights_html = ""
        if ai_report:
            insights_items = "".join(
                f"<li>{html_lib.escape(i)}</li>" for i in ai_report.insights
            )
            risk_items = "".join(
                f"<li>{html_lib.escape(f)}</li>" for f in ai_report.risk_flags
            )
            tags_str = html_lib.escape(", ".join(ai_report.tags))
            insights_html = f"""
            <section class="ai-section">
                <h2>Análise de IA</h2>
                <div class="summary">{html_lib.escape(ai_report.summary)}</div>
                <h3>{html_lib.escape(ai_report.profile_type)}</h3>
                <div class="score">Score: {ai_report.digital_footprint_score}/10</div>
                <div class="insights">
                    <h4>Insights:</h4>
                    <ul>{insights_items}</ul>
                </div>
                <div class="risks">
                    <h4>Risk Flags:</h4>
                    <ul>{risk_items}</ul>
                </div>
                <div class="tags"><strong>Tags:</strong> {tags_str}</div>
            </section>
            """

        html = f"""<!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <title>ARGUS: {safe_target}</title>
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
                <h1>ARGUS: {safe_target}</h1>
                <div class="platforms"><h2>Plataformas ({len(results)})</h2>{platforms_html}</div>
                {insights_html}
            </div>
        </body>
        </html>"""
        return html

    @staticmethod
    def to_cli(target: str, results: List[Dict], ai_report: Optional[AIReport] = None):
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel

        console = Console()
        console.print(f"\n[bold cyan]ARGUS: {target}[/bold cyan]\n")

        table = Table(title="Plataformas Encontradas")
        table.add_column("Site", style="cyan")
        table.add_column("Categoria", style="magenta")

        for r in results:
            table.add_row(r["site_name"], r.get("metadata", {}).get("category", "unknown"))

        console.print(table)

        if ai_report:
            console.print(Panel(
                f"[bold]{ai_report.profile_type}[/bold]\n{ai_report.summary}",
                title="Análise"
            ))
            console.print(f"\n[bold yellow]Score: {ai_report.digital_footprint_score}/10[/bold yellow]")
