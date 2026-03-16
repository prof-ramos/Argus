import json
from typing import Optional

from openai import OpenAI

from ai.models import AIReport
from ai.prompt_builder import PromptBuilder
from config.settings import LLM_MODEL, LLM_TEMPERATURE, OPENAI_API_KEY


class ReportGenerator:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = LLM_MODEL

    def generate(
        self,
        username: str,
        results: list,
        search_type: str = "username",
    ) -> Optional[AIReport]:
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY nao configurada")

        prompt = PromptBuilder.build(username, results, search_type)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=LLM_TEMPERATURE,
                response_format={"type": "json_object"},
            )
            report_data = json.loads(response.choices[0].message.content or "{}")
            return AIReport(
                summary=report_data.get("summary", ""),
                profile_type=report_data.get("profile_type", "Unknown"),
                insights=report_data.get("insights", []),
                risk_flags=report_data.get("risk_flags", []),
                tags=report_data.get("tags", []),
                digital_footprint_score=report_data.get("digital_footprint_score", 5),
                confidence=report_data.get("confidence", "baixa"),
                platforms_found=len(results),
                high_value_platforms=[
                    result["site_name"]
                    for result in results
                    if result["metadata"]["data_richness"] == "high"
                ],
                categories=sorted({result["metadata"]["category"] for result in results}),
            )
        except Exception as exc:
            print(f"Erro ao gerar relatorio com IA: {exc}")
            return None
