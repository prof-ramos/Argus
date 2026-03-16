from typing import List

from collectors.base import AccountResult, ResultStatus


class Normalizer:
    @staticmethod
    def normalize(all_results: List[List[AccountResult]]) -> List[AccountResult]:
        normalized: List[AccountResult] = []
        seen: set[tuple[str, str, str]] = set()

        for results in all_results:
            for result in results:
                dedupe_key = (
                    result.site_name,
                    result.url or "",
                    result.status.value,
                )
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)
                normalized.append(result)

        return normalized

    @staticmethod
    def summarize(results: List[AccountResult]) -> dict:
        collector_names = {"Maigret", "Holehe"}
        collectors_run = sum(1 for result in results if result.site_name in collector_names)
        collector_failures = sum(
            1
            for result in results
            if result.site_name in collector_names and result.status in {ResultStatus.ERROR, ResultStatus.TIMEOUT}
        )
        found_results = sum(1 for result in results if result.status == ResultStatus.FOUND)

        return {
            "collectors_run": collectors_run,
            "collector_failures": collector_failures,
            "found_results": found_results,
        }
