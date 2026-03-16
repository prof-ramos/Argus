import json
from typing import Optional, List, Dict
from openai import OpenAI
from ai.models import AIReport
from ai.prompt_builder import PromptBuilder
from config.settings import OPENAI_API_KEY, LLM_MODEL, LLM_TEMPERATURE


class ReportGenerator:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = LLM_MODEL

    def generate(self, username: str, results: List[Dict], search_type: str = "username") -> Optional[AIReport]:
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
            print(f"Erro: {e}")
            return None
