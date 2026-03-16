"""
E2E tests for ARGUS AI analysis integration via --ai flag.

Tests that:
- --ai triggers the ReportGenerator
- AI report content appears in CLI, JSON, and HTML outputs
- Missing API key produces a clean error exit
"""
import json
import pytest
from unittest.mock import patch
from argus import app


def _set_api_key(monkeypatch, key):
    """Patch OPENAI_API_KEY in both settings and argus module (imported at module level)."""
    import config.settings as settings
    import argus as argus_module
    monkeypatch.setattr(settings, "OPENAI_API_KEY", key)
    monkeypatch.setattr(argus_module, "OPENAI_API_KEY", key)


class TestAiFlag:

    def test_ai_flag_calls_report_generator(
        self, runner, mock_maigret_collect, mock_filter_passthrough,
        mock_ai_generate, tmp_output_dir, monkeypatch
    ):
        """--ai flag triggers ReportGenerator.generate exactly once."""
        _set_api_key(monkeypatch, "sk-test-key")

        result = runner.invoke(
            app, ["search", "--username", "testuser", "--ai"]
        )
        assert result.exit_code == 0
        mock_ai_generate.assert_called_once()

    def test_ai_report_shows_profile_type_in_cli(
        self, runner, mock_maigret_collect, mock_filter_passthrough,
        mock_ai_generate, sample_ai_report, tmp_output_dir, monkeypatch
    ):
        """AI profile_type appears in CLI output when --ai is used."""
        _set_api_key(monkeypatch, "sk-test-key")

        result = runner.invoke(
            app, ["search", "--username", "testuser", "--ai"]
        )
        assert result.exit_code == 0
        assert sample_ai_report.profile_type in result.output

    def test_ai_report_shows_score_in_cli(
        self, runner, mock_maigret_collect, mock_filter_passthrough,
        mock_ai_generate, sample_ai_report, tmp_output_dir, monkeypatch
    ):
        """AI digital_footprint_score appears in CLI output."""
        _set_api_key(monkeypatch, "sk-test-key")

        result = runner.invoke(
            app, ["search", "--username", "testuser", "--ai"]
        )
        assert result.exit_code == 0
        assert str(sample_ai_report.digital_footprint_score) in result.output

    def test_ai_report_in_json_output(
        self, runner, mock_maigret_collect, mock_filter_passthrough,
        mock_ai_generate, sample_ai_report, tmp_output_dir, monkeypatch
    ):
        """ai_analysis field is populated in JSON output when --ai is used."""
        _set_api_key(monkeypatch, "sk-test-key")

        result = runner.invoke(
            app, ["search", "--username", "testuser", "--ai", "--format", "json"]
        )
        assert result.exit_code == 0
        json_text = result.output.split("Salvo:")[0].strip()
        parsed = json.loads(json_text)

        assert parsed["ai_analysis"] is not None
        assert parsed["ai_analysis"]["profile_type"] == sample_ai_report.profile_type
        assert parsed["ai_analysis"]["digital_footprint_score"] == sample_ai_report.digital_footprint_score

    def test_ai_report_in_html_output(
        self, runner, mock_maigret_collect, mock_filter_passthrough,
        mock_ai_generate, sample_ai_report, tmp_output_dir, monkeypatch
    ):
        """AI analysis section appears in HTML when --ai is used."""
        _set_api_key(monkeypatch, "sk-test-key")

        runner.invoke(
            app, ["search", "--username", "testuser", "--ai", "--format", "html"]
        )
        html_file = next(tmp_output_dir.glob("*.html"))
        content = html_file.read_text(encoding="utf-8")

        assert '<section class="ai-section">' in content
        assert sample_ai_report.profile_type in content
        assert "Análise de IA" in content

    def test_ai_insights_in_html(
        self, runner, mock_maigret_collect, mock_filter_passthrough,
        mock_ai_generate, sample_ai_report, tmp_output_dir, monkeypatch
    ):
        """AI insights list items appear in the HTML report."""
        _set_api_key(monkeypatch, "sk-test-key")

        runner.invoke(
            app, ["search", "--username", "testuser", "--ai", "--format", "html"]
        )
        html_file = next(tmp_output_dir.glob("*.html"))
        content = html_file.read_text(encoding="utf-8")

        for insight in sample_ai_report.insights:
            assert insight in content


class TestAiErrors:

    def test_ai_without_api_key_exits_with_error(
        self, runner, tmp_output_dir, monkeypatch
    ):
        """--ai without OPENAI_API_KEY exits with code 1 and error message."""
        _set_api_key(monkeypatch, None)

        result = runner.invoke(
            app, ["search", "--username", "testuser", "--ai"]
        )
        assert result.exit_code == 1

    def test_ai_with_inline_api_key_accepted(
        self, runner, mock_maigret_collect, mock_filter_passthrough,
        mock_ai_generate, tmp_output_dir, monkeypatch
    ):
        """--api-key flag is accepted as alternative to env variable."""
        _set_api_key(monkeypatch, None)

        result = runner.invoke(
            app, ["search", "--username", "testuser", "--ai", "--api-key", "sk-inline-key"]
        )
        # api_key param is truthy, so the check passes
        assert result.exit_code == 0
