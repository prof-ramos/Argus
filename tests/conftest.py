"""
Shared fixtures for ARGUS E2E tests.
"""
import copy
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typer.testing import CliRunner

from collectors.base import AccountResult, ResultStatus
from ai.models import AIReport


# ---------------------------------------------------------------------------
# Sample data fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_maigret_results():
    """Simulated results from MaigreCollector (username search)."""
    return [
        AccountResult(
            site_name="GitHub",
            url="https://github.com/testuser",
            status=ResultStatus.FOUND,
            http_status=200,
            metadata={"found": True, "status_code": 200}
        ),
        AccountResult(
            site_name="Twitter",
            url="https://twitter.com/testuser",
            status=ResultStatus.FOUND,
            http_status=200,
            metadata={"found": True, "status_code": 200}
        ),
        AccountResult(
            site_name="Reddit",
            url="https://reddit.com/u/testuser",
            status=ResultStatus.FOUND,
            http_status=200,
            metadata={"found": True, "status_code": 200}
        ),
    ]


@pytest.fixture
def sample_holehe_results():
    """Simulated results from HoleheCollector (email search)."""
    return [
        AccountResult(
            site_name="Spotify",
            url=None,
            status=ResultStatus.FOUND,
            http_status=200,
            metadata={}
        ),
        AccountResult(
            site_name="LinkedIn",
            url=None,
            status=ResultStatus.FOUND,
            http_status=200,
            metadata={}
        ),
    ]


@pytest.fixture
def sample_ai_report():
    """A fully populated AIReport for testing AI output."""
    return AIReport(
        summary="Usuário com forte presença digital em plataformas de desenvolvimento e redes sociais.",
        profile_type="Desenvolvedor Ativo",
        insights=["Presença em GitHub indica desenvolvedor ativo", "Twitter sugere engajamento social"],
        risk_flags=["Alta exposição de dados públicos"],
        tags=["developer", "social", "tech"],
        digital_footprint_score=7,
        confidence="medium",
        platforms_found=3,
        high_value_platforms=["GitHub", "Twitter", "Reddit"],
        categories=["developer", "social"]
    )


# ---------------------------------------------------------------------------
# CLI runner fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def runner():
    """Typer CLI test runner."""
    return CliRunner()


# ---------------------------------------------------------------------------
# Patch helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_maigret_collect(sample_maigret_results):
    """Patch MaigreCollector.collect to return sample results."""
    with patch(
        "collectors.maigret.MaigreCollector.collect",
        new_callable=AsyncMock,
        return_value=sample_maigret_results
    ) as mock:
        yield mock


@pytest.fixture
def mock_holehe_collect(sample_holehe_results):
    """Patch HoleheCollector.collect to return sample results."""
    with patch(
        "collectors.holehe.HoleheCollector.collect",
        new_callable=AsyncMock,
        return_value=sample_holehe_results
    ) as mock:
        yield mock


@pytest.fixture
def mock_filter_passthrough():
    """Patch FalsePositiveFilter._validate_single to return a copy of the result (no HTTP calls)."""
    async def passthrough(self, session, result):
        result_copy = copy.copy(result)
        if result_copy.status == ResultStatus.FOUND:
            result_copy.http_status = 200
        return result_copy

    with patch(
        "processing.filter.FalsePositiveFilter._validate_single",
        new=passthrough
    ):
        yield


@pytest.fixture
def mock_ai_generate(sample_ai_report):
    """Patch ReportGenerator in argus module to return a canned AIReport.

    Patches the class itself so that __init__ (which creates an OpenAI client)
    is never called, and generate() returns the sample report.
    """
    mock_instance = MagicMock()
    mock_instance.generate.return_value = sample_ai_report
    with patch("argus.ReportGenerator", return_value=mock_instance):
        yield mock_instance.generate


# ---------------------------------------------------------------------------
# Temporary output directory
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def tmp_output_dir(tmp_path, monkeypatch):
    """Redirect ARGUS output directory to a temp folder for each test."""
    import config.settings as settings
    import argus as argus_module
    monkeypatch.setattr(settings, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(argus_module, "OUTPUT_DIR", tmp_path)
    return tmp_path
