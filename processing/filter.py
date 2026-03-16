import asyncio
from typing import List, Optional

import aiohttp

from collectors.base import AccountResult, ResultStatus
from config.settings import FALSE_POSITIVE_SITES, VALIDATE_URLS, VALIDATION_TIMEOUT


class FalsePositiveFilter:
    def __init__(self) -> None:
        self.blocklist = FALSE_POSITIVE_SITES

    async def filter(self, results: List[AccountResult]) -> List[AccountResult]:
        if not VALIDATE_URLS:
            return results

        validated = await asyncio.gather(
            *(self._validate_single(result) for result in results)
        )
        return [result for result in validated if result is not None]

    async def _validate_single(self, result: AccountResult) -> Optional[AccountResult]:
        if result.status != ResultStatus.FOUND or not result.url:
            return result

        if any(site in result.url for site in self.blocklist):
            return None

        try:
            timeout = aiohttp.ClientTimeout(total=VALIDATION_TIMEOUT)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(result.url, allow_redirects=True) as response:
                    if response.status == 200:
                        result.http_status = 200
                        return result
        except Exception:
            return None
        return None
