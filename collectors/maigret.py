import asyncio
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import List

from config.settings import COLLECTOR_TIMEOUT, MAIGRET_TOP_SITES

from .base import AccountResult, ResultStatus


class MaigreCollector:
    def __init__(self) -> None:
        self.name = "Maigret"
        self.command = "maigret"

    async def collect(self, username: str) -> List[AccountResult]:
        try:
            result = await asyncio.wait_for(
                self._run_maigret(username),
                timeout=COLLECTOR_TIMEOUT,
            )
            return self._parse_results(result)
        except asyncio.TimeoutError:
            return [AccountResult(site_name=self.name, status=ResultStatus.TIMEOUT, error="Timeout")]
        except Exception as exc:
            return [AccountResult(site_name=self.name, status=ResultStatus.ERROR, error=str(exc))]

    async def _run_maigret(self, username: str) -> dict:
        executable = self._resolve_executable()
        output_dir = Path(tempfile.mkdtemp(prefix=f"maigret_{username}_"))

        try:
            proc = await asyncio.create_subprocess_exec(
                executable,
                username,
                "-J",
                "simple",
                "-fo",
                str(output_dir),
                "--top-sites",
                str(MAIGRET_TOP_SITES),
                "--no-progressbar",
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

            report_files = sorted(output_dir.glob("*.json"))
            if not report_files:
                raise RuntimeError(f"{self.command} nao gerou arquivo JSON de saida")

            raw = report_files[0].read_text()
            if not raw.strip():
                return {"results": {}}

            return json.loads(raw)
        finally:
            for file in output_dir.glob("*"):
                file.unlink(missing_ok=True)
            output_dir.rmdir()

    def _parse_results(self, maigret_output: dict) -> List[AccountResult]:
        results: List[AccountResult] = []
        for site_name, site_data in maigret_output.items():
            if not isinstance(site_data, dict):
                continue

            status_block = site_data.get("status", {})
            claimed = (
                isinstance(status_block, dict)
                and status_block.get("status") == "Claimed"
            )

            results.append(
                AccountResult(
                    site_name=site_name,
                    url=site_data.get("url_user") or (status_block.get("url") if isinstance(status_block, dict) else None),
                    status=ResultStatus.FOUND if claimed else ResultStatus.NOT_FOUND,
                    http_status=site_data.get("http_status"),
                    metadata=site_data,
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
