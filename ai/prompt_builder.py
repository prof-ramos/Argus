from typing import List, Dict


class PromptBuilder:
    @staticmethod
    def build(target: str, results: List[Dict], search_type: str = "username") -> str:
        platforms = [r["site_name"] for r in results]
        categories = sorted(set(
            r.get("metadata", {}).get("category", "unknown") for r in results
        ))
        high_value = [
            r["site_name"] for r in results
            if r.get("metadata", {}).get("data_richness") == "high"
        ]

        return f"""You are an OSINT analyst specializing in behavioral profiling.

Based SOLELY on the list of platforms where a target was found, generate a structured intelligence report.

Target: {target}
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
