import asyncio
import re
from typing import List
from .base import AccountResult, ResultStatus
from config.settings import COLLECTOR_TIMEOUT


class HoleheCollector:
    def __init__(self):
        self.name = "Holehe"

    async def collect(self, email: str) -> List[AccountResult]:
        try:
            result = await asyncio.wait_for(
                self._run_holehe(email),
                timeout=COLLECTOR_TIMEOUT
            )
            return self._parse_results(result, email)
        except asyncio.TimeoutError:
            return [AccountResult(
                site_name="Holehe",
                status=ResultStatus.TIMEOUT,
                error="Timeout"
            )]
        except Exception as e:
            return [AccountResult(
                site_name="Holehe",
                status=ResultStatus.ERROR,
                error=str(e)
            )]

    async def _run_holehe(self, email: str) -> str:
        proc = await asyncio.create_subprocess_exec(
            "holehe", email, "--only-used", "--no-color",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, _ = await proc.communicate()
        return stdout.decode('utf-8', errors='ignore')

    def _parse_results(self, output: str, email: str) -> List[AccountResult]:
        results = []
        pattern = r"(.+?)\s*:\s*(found|not found)"
        matches = re.findall(pattern, output, re.IGNORECASE)

        for site_name, status in matches:
            results.append(AccountResult(
                site_name=site_name.strip(),
                status=ResultStatus.FOUND if status.lower() == "found" else ResultStatus.NOT_FOUND,
                http_status=200 if status.lower() == "found" else 404
            ))

        return results
