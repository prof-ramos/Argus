import json
import asyncio
import tempfile
import os
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
        except (OSError, ValueError) as e:
            return [AccountResult(
                site_name="Maigret",
                status=ResultStatus.ERROR,
                error=str(e)
            )]
        except Exception as e:
            return [AccountResult(
                site_name="Maigret",
                status=ResultStatus.ERROR,
                error=f"{type(e).__name__}: {e}"
            )]

    async def _run_maigret(self, username: str) -> dict:
        fd, output_file = tempfile.mkstemp(suffix=".json", prefix="maigret_")
        os.close(fd)

        try:
            proc = await asyncio.create_subprocess_exec(
                "maigret", username, "--json", "--output", output_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()

            loop = asyncio.get_event_loop()
            try:
                content = await loop.run_in_executor(
                    None, lambda: open(output_file).read()
                )
                return json.loads(content)
            except (OSError, json.JSONDecodeError):
                return {"results": {}}
        finally:
            try:
                os.unlink(output_file)
            except OSError:
                pass

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
