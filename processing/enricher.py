import json
import logging
from typing import List, Dict
from collectors.base import AccountResult
from config.settings import BASE_DIR

logger = logging.getLogger(__name__)


class Enricher:
    def __init__(self):
        metadata_path = BASE_DIR / "config" / "platforms_metadata.json"
        try:
            with open(metadata_path, encoding="utf-8") as f:
                raw = json.load(f)
                self.platform_data = raw["platforms"]
                self.aliases: Dict[str, str] = raw.get("aliases", {})
        except (OSError, json.JSONDecodeError, KeyError) as e:
            logger.warning("Could not load platforms_metadata.json: %s. Using empty metadata.", e)
            self.platform_data = {}
            self.aliases = {}

    def enrich(self, results: List[AccountResult]) -> List[Dict]:
        enriched = []

        for result in results:
            site_key = result.site_name.lower().replace(" ", "-").replace(".", "")
            site_key = self.aliases.get(site_key, site_key)
            platform_meta = self.platform_data.get(site_key, {})

            enriched.append({
                "site_name": result.site_name,
                "url": result.url,
                "status": result.status.value,
                "http_status": result.http_status,
                "metadata": {
                    **result.metadata,
                    "category": platform_meta.get("category", "unknown"),
                    "data_richness": platform_meta.get("data_richness", "low"),
                    "description": platform_meta.get("description", "")
                }
            })

        return enriched
