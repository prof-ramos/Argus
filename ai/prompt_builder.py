from typing import Dict, List


class PromptBuilder:
    @staticmethod
    def build(username: str, results: List[Dict], search_type: str = "username") -> str:
        platforms = [result["site_name"] for result in results]
        categories = sorted({result["metadata"]["category"] for result in results})
        high_value = [
            result["site_name"]
            for result in results
            if result["metadata"]["data_richness"] == "high"
        ]

        return f"""Voce e um analista OSINT especializado em perfil comportamental.

Baseado SOMENTE na lista de plataformas confirmadas, gere um relatorio estruturado.

Alvo: {username}
Tipo de busca: {search_type}
Plataformas confirmadas ({len(platforms)}): {", ".join(platforms) if platforms else "nenhuma"}
Plataformas de alto valor: {", ".join(high_value) if high_value else "nenhuma"}
Categorias: {", ".join(categories) if categories else "nenhuma"}

Nao invente fatos. Responda em portugues do Brasil.
Retorne JSON valido com exatamente estes campos:
{{
  "summary": "resumo em 2-3 frases",
  "profile_type": "rotulo descritivo",
  "insights": ["insight 1", "insight 2"],
  "risk_flags": ["risco 1", "risco 2"],
  "tags": ["tag1", "tag2"],
  "digital_footprint_score": 5,
  "confidence": "media"
}}"""
