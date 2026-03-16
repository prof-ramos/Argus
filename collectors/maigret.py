import json
import asyncio
from typing import List
from .base import AccountResult, ResultStatus
from config.settings import COLLECTOR_TIMEOUT


class MaigreCollector:
    def __init__(self):
        self.name = "Maigret"

    async def collect(self, username: str) -> List[AccountResult]:
        try:
            result = await asyncio.wait_for(
                self._run_maigret(username),
                timeout=COLLECTOR_TIMEOUT
            )
            return self._parse_results(result)
        except asyncio.TimeoutError:
            return [AccountResult(
                site_name="Maigret",
                status=ResultStatus.TIMEOUT,
                error="Timeout"
            )]
        except Exception as e:
            return [AccountResult(
                site_name="Maigret",
                status=ResultStatus.ERROR,
                error=str(e)
            )]

    async def _run_maigret(self, username: str) -> dict:
        output_file = f"/tmp/maigret_{username}.json"

        proc = await asyncio.create_subprocess_exec(
            "maigret", username, "--json", "--output", output_file,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        await proc.communicate()

        try:
            with open(output_file) as f:
                return json.load(f)
        except Exception:
            return {"results": {}}

    def _parse_results(self, maigret_output: dict) -> List[AccountResult]:
        results = []

        for username_data in maigret_output.get("results", {}).values():
            for site_name, site_data in username_data.items():
                if isinstance(site_data, dict):
                    status = ResultStatus.FOUND if site_data.get("found") else ResultStatus.NOT_FOUND
                    results.append(AccountResult(
                        site_name=site_name,
                        url=site_data.get("url"),
                        status=status,
                        http_status=site_data.get("status_code"),
                        metadata=site_data
                    ))

        return results
