import asyncio
import copy
import logging
import aiohttp
from typing import List, Optional
from urllib.parse import urlparse
from collectors.base import AccountResult, ResultStatus
from config.settings import VALIDATE_URLS, VALIDATION_TIMEOUT, FALSE_POSITIVE_SITES

logger = logging.getLogger(__name__)


class FalsePositiveFilter:
    def __init__(self):
        self.blocklist = FALSE_POSITIVE_SITES

    async def filter(self, results: List[AccountResult]) -> List[AccountResult]:
        if not VALIDATE_URLS:
            return results

        connector = aiohttp.TCPConnector(limit=20)
        timeout = aiohttp.ClientTimeout(total=VALIDATION_TIMEOUT)

        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            tasks = [self._validate_single(session, r) for r in results]
            validated = await asyncio.gather(*tasks)

        return [r for r in validated if r is not None]

    async def _validate_single(
        self, session: aiohttp.ClientSession, result: AccountResult
    ) -> Optional[AccountResult]:
        if result.status != ResultStatus.FOUND or not result.url:
            return result

        if any(fp in result.url for fp in self.blocklist):
            return None

        try:
            async with session.get(result.url, allow_redirects=True) as resp:
                final_url = str(resp.url)
                if _is_404_redirect(final_url):
                    return None
                if resp.status == 200:
                    validated = copy.copy(result)
                    validated.http_status = 200
                    return validated
                return None
        except Exception as e:
            logger.debug("Validation failed for %s: %s: %s", result.url, type(e).__name__, e)
            return None


def _is_404_redirect(url: str) -> bool:
    """Return True if the final URL looks like a 404/not-found redirect."""
    path = urlparse(url).path.lower()
    return "404" in path or "not-found" in path or "notfound" in path
