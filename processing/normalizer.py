from typing import List
from collectors.base import AccountResult


class Normalizer:
    @staticmethod
    def normalize(all_results: List[List[AccountResult]]) -> List[AccountResult]:
        flattened = []

        for results in all_results:
            flattened.extend(results)

        seen = set()
        normalized = []

        seen_urls = set()
        for result in flattened:
            key = (result.site_name, result.url)
            if key not in seen and result.url and result.url not in seen_urls:
                seen.add(key)
                seen_urls.add(result.url)
                normalized.append(result)

        return normalized
