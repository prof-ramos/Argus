import asyncio
import aiohttp
from typing import List, Optional
from collectors.base import AccountResult, ResultStatus
from config.settings import VALIDATE_URLS, VALIDATION_TIMEOUT, FALSE_POSITIVE_SITES


class FalsePositiveFilter:
    def __init__(self):
        self.blocklist = FALSE_POSITIVE_SITES

    async def filter(self, results: List[AccountResult]) -> List[AccountResult]:
        if not VALIDATE_URLS:
            return results

        tasks = [self._validate_single(r) for r in results]
        validated = await asyncio.gather(*tasks)

        return [r for r in validated if r is not None]

    async def _validate_single(self, result: AccountResult) -> Optional[AccountResult]:
        if result.status != ResultStatus.FOUND or not result.url:
            return result

        if any(fp in result.url for fp in self.blocklist):
            return None

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    result.url,
                    timeout=aiohttp.ClientTimeout(total=VALIDATION_TIMEOUT),
                    allow_redirects=True
                ) as resp:
                    if resp.url != result.url and "404" not in str(resp.url):
                        return None

                    if resp.status == 200:
                        result.http_status = 200
                        return result
                    else:
                        return None
        except Exception:
            return None
