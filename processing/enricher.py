import json
from typing import Dict, List

from collectors.base import AccountResult
from config.settings import BASE_DIR


class Enricher:
    def __init__(self) -> None:
        metadata_path = BASE_DIR / "config" / "platforms_metadata.json"
        self.platform_data = json.loads(metadata_path.read_text())["platforms"]

    def enrich(self, results: List[AccountResult]) -> List[Dict]:
        enriched = []
        for result in results:
            site_key = result.site_name.lower().replace(" ", "-").replace(".", "")
            platform_meta = self.platform_data.get(site_key, {})
            enriched.append(
                {
                    "site_name": result.site_name,
                    "url": result.url,
                    "status": result.status.value,
                    "http_status": result.http_status,
                    "error": result.error,
                    "metadata": {
                        **result.metadata,
                        "category": platform_meta.get("category", "unknown"),
                        "data_richness": platform_meta.get("data_richness", "low"),
                        "description": platform_meta.get("description", ""),
                    },
                }
            )
        return enriched
