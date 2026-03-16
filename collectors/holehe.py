import asyncio
import os
import re
import shutil
from pathlib import Path
from typing import List

from config.settings import COLLECTOR_TIMEOUT

from .base import AccountResult, ResultStatus


class HoleheCollector:
    def __init__(self) -> None:
        self.name = "Holehe"
        self.command = "holehe"

    async def collect(self, email: str) -> List[AccountResult]:
        try:
            result = await asyncio.wait_for(
                self._run_holehe(email),
                timeout=COLLECTOR_TIMEOUT,
            )
            return self._parse_results(result)
        except asyncio.TimeoutError:
            return [AccountResult(site_name=self.name, status=ResultStatus.TIMEOUT, error="Timeout")]
        except Exception as exc:
            return [AccountResult(site_name=self.name, status=ResultStatus.ERROR, error=str(exc))]

    async def _run_holehe(self, email: str) -> str:
        executable = self._resolve_executable()
        proc = await asyncio.create_subprocess_exec(
            executable,
            email,
            "--only-used",
            "--no-color",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            error_msg = stderr.decode("utf-8", errors="ignore").strip()
            if not error_msg:
                error_msg = stdout.decode("utf-8", errors="ignore").strip()
            raise RuntimeError(error_msg or f"{self.command} falhou com exit code {proc.returncode}")
        return stdout.decode("utf-8", errors="ignore")

    def _parse_results(self, output: str) -> List[AccountResult]:
        results: List[AccountResult] = []

        modern_pattern = r"^\[\+\]\s+(.+)$"
        modern_matches = re.findall(modern_pattern, output, re.MULTILINE)
        if modern_matches:
            for site_name in modern_matches:
                cleaned_name = site_name.split(" / ", 1)[0].strip()
                if "Email used" in cleaned_name:
                    continue
                results.append(
                    AccountResult(
                        site_name=cleaned_name,
                        status=ResultStatus.FOUND,
                        http_status=200,
                    )
                )
            return results

        legacy_pattern = r"(.+?)\s*:\s*(found|not found)"
        for site_name, status in re.findall(legacy_pattern, output, re.IGNORECASE):
            found = status.lower() == "found"
            results.append(
                AccountResult(
                    site_name=site_name.strip(),
                    status=ResultStatus.FOUND if found else ResultStatus.NOT_FOUND,
                    http_status=200 if found else 404,
                )
            )
        return results

    def _resolve_executable(self) -> str:
        executable = shutil.which(self.command)
        if executable:
            return executable

        venv = os.environ.get("VIRTUAL_ENV")
        if venv:
            candidate = Path(venv) / "bin" / self.command
            if candidate.exists():
                return str(candidate)

        raise FileNotFoundError(f"{self.command} nao instalado no ambiente do projeto")
