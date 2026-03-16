import json
import logging
from typing import Optional, List, Dict
from ai.models import AIReport
from ai.prompt_builder import PromptBuilder
from config.settings import OPENAI_API_KEY, LLM_MODEL, LLM_TEMPERATURE

logger = logging.getLogger(__name__)


class ReportGenerator:
    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or OPENAI_API_KEY
        self._client = None
        self.model = LLM_MODEL

    @property
    def client(self) -> "OpenAI":
        """Lazy-initialize OpenAI client only when first needed."""
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def generate(self, username: str, results: List[Dict], search_type: str = "username") -> Optional[AIReport]:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not configured")

        prompt = PromptBuilder.build(username, results, search_type)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=LLM_TEMPERATURE,
                response_format={"type": "json_object"}
            )

            choices = response.choices
            if not choices:
                logger.error("OpenAI returned empty choices list")
                return None

            content = choices[0].message.content
            try:
                report_data = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error("Failed to parse OpenAI JSON response: %s", e)
                return None

            return AIReport(
                summary=report_data.get("summary", ""),
                profile_type=report_data.get("profile_type", "Unknown"),
                insights=report_data.get("insights", []),
                risk_flags=report_data.get("risk_flags", []),
                tags=report_data.get("tags", []),
                digital_footprint_score=report_data.get("digital_footprint_score", 5),
                confidence=report_data.get("confidence", "low"),
                platforms_found=len(results),
                high_value_platforms=[
                    r["site_name"] for r in results
                    if r.get("metadata", {}).get("data_richness") == "high"
                ],
                categories=sorted(set(
                    r.get("metadata", {}).get("category", "unknown") for r in results
                ))
            )

        except Exception as e:
            logger.error("ReportGenerator error: %s: %s", type(e).__name__, e)
            return None
