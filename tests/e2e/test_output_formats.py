"""
E2E tests for ARGUS output formats: JSON and HTML.

Verifies that:
- --format json produces valid, well-structured JSON output
- --format html produces valid HTML output with expected content
- Default format (cli) does not produce a saved file
"""
import json
import pytest
from argus import app


class TestJsonFormat:

    def test_json_format_exits_successfully(
        self, runner, mock_maigret_collect, mock_filter_passthrough, tmp_output_dir
    ):
        """--format json exits with code 0."""
        result = runner.invoke(
            app, ["search", "--username", "testuser", "--format", "json"]
        )
        assert result.exit_code == 0

    def test_json_format_is_valid_json(
        self, runner, mock_maigret_collect, mock_filter_passthrough, tmp_output_dir
    ):
        """stdout contains parseable JSON when --format json is used."""
        result = runner.invoke(
            app, ["search", "--username", "testuser", "--format", "json"]
        )
        # stdout contains JSON block before the "Salvo:" message
        json_text = result.output.split("Salvo:")[0].strip()
        parsed = json.loads(json_text)
        assert isinstance(parsed, dict)

    def test_json_format_contains_required_fields(
        self, runner, mock_maigret_collect, mock_filter_passthrough, tmp_output_dir
    ):
        """JSON output contains the fields: target, platforms_found, platforms."""
        result = runner.invoke(
            app, ["search", "--username", "testuser", "--format", "json"]
        )
        json_text = result.output.split("Salvo:")[0].strip()
        parsed = json.loads(json_text)

        assert "target" in parsed
        assert "platforms_found" in parsed
        assert "platforms" in parsed
        assert parsed["target"] == "testuser"

    def test_json_format_platforms_list_has_correct_structure(
        self, runner, mock_maigret_collect, mock_filter_passthrough, tmp_output_dir
    ):
        """Each platform entry in JSON has site_name, url, status, metadata."""
        result = runner.invoke(
            app, ["search", "--username", "testuser", "--format", "json"]
        )
        json_text = result.output.split("Salvo:")[0].strip()
        parsed = json.loads(json_text)

        for platform in parsed["platforms"]:
            assert "site_name" in platform
            assert "url" in platform
            assert "status" in platform
            assert "metadata" in platform

    def test_json_format_saves_file_to_output_dir(
        self, runner, mock_maigret_collect, mock_filter_passthrough, tmp_output_dir
    ):
        """A .json report file is saved in the OUTPUT_DIR."""
        runner.invoke(
            app, ["search", "--username", "testuser", "--format", "json"]
        )
        json_files = list(tmp_output_dir.glob("*.json"))
        assert len(json_files) == 1
        assert "testuser" in json_files[0].name

    def test_json_format_saved_file_is_valid_json(
        self, runner, mock_maigret_collect, mock_filter_passthrough, tmp_output_dir
    ):
        """The saved .json file is parseable and has the correct structure."""
        runner.invoke(
            app, ["search", "--username", "testuser", "--format", "json"]
        )
        json_file = next(tmp_output_dir.glob("*.json"))
        parsed = json.loads(json_file.read_text(encoding="utf-8"))
        assert parsed["target"] == "testuser"
        assert isinstance(parsed["platforms"], list)

    def test_json_ai_analysis_is_null_without_ai_flag(
        self, runner, mock_maigret_collect, mock_filter_passthrough, tmp_output_dir
    ):
        """Without --ai flag, ai_analysis field is null in JSON output."""
        result = runner.invoke(
            app, ["search", "--username", "testuser", "--format", "json"]
        )
        json_text = result.output.split("Salvo:")[0].strip()
        parsed = json.loads(json_text)
        assert parsed.get("ai_analysis") is None


class TestHtmlFormat:

    def test_html_format_exits_successfully(
        self, runner, mock_maigret_collect, mock_filter_passthrough, tmp_output_dir
    ):
        """--format html exits with code 0."""
        result = runner.invoke(
            app, ["search", "--username", "testuser", "--format", "html"]
        )
        assert result.exit_code == 0

    def test_html_format_saves_file_to_output_dir(
        self, runner, mock_maigret_collect, mock_filter_passthrough, tmp_output_dir
    ):
        """A .html report file is saved in the OUTPUT_DIR."""
        runner.invoke(
            app, ["search", "--username", "testuser", "--format", "html"]
        )
        html_files = list(tmp_output_dir.glob("*.html"))
        assert len(html_files) == 1
        assert "testuser" in html_files[0].name

    def test_html_format_contains_doctype(
        self, runner, mock_maigret_collect, mock_filter_passthrough, tmp_output_dir
    ):
        """Saved HTML file starts with DOCTYPE declaration."""
        runner.invoke(
            app, ["search", "--username", "testuser", "--format", "html"]
        )
        html_file = next(tmp_output_dir.glob("*.html"))
        content = html_file.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content

    def test_html_format_contains_username_in_title(
        self, runner, mock_maigret_collect, mock_filter_passthrough, tmp_output_dir
    ):
        """Saved HTML title tag includes the searched username."""
        runner.invoke(
            app, ["search", "--username", "testuser", "--format", "html"]
        )
        html_file = next(tmp_output_dir.glob("*.html"))
        content = html_file.read_text(encoding="utf-8")
        assert "testuser" in content
        assert "<title>" in content

    def test_html_format_contains_platform_names(
        self, runner, mock_maigret_collect, mock_filter_passthrough, tmp_output_dir
    ):
        """Platform names from the collector appear in the HTML body."""
        runner.invoke(
            app, ["search", "--username", "testuser", "--format", "html"]
        )
        html_file = next(tmp_output_dir.glob("*.html"))
        content = html_file.read_text(encoding="utf-8")
        assert "GitHub" in content
        assert "Twitter" in content
        assert "Reddit" in content

    def test_html_no_ai_section_without_ai_flag(
        self, runner, mock_maigret_collect, mock_filter_passthrough, tmp_output_dir
    ):
        """HTML does not contain the AI analysis <section> element when --ai is not used."""
        runner.invoke(
            app, ["search", "--username", "testuser", "--format", "html"]
        )
        html_file = next(tmp_output_dir.glob("*.html"))
        content = html_file.read_text(encoding="utf-8")
        # The CSS class .ai-section is always present, but the actual <section> element
        # should only appear when AI analysis is run
        assert '<section class="ai-section">' not in content
        assert "Análise de IA" not in content


class TestCliFormat:

    def test_cli_is_default_format(
        self, runner, mock_maigret_collect, mock_filter_passthrough, tmp_output_dir
    ):
        """Without --format, CLI format is used (no file saved)."""
        runner.invoke(app, ["search", "--username", "testuser"])
        # No JSON or HTML file should be saved for CLI format
        saved_files = list(tmp_output_dir.glob("*.*"))
        assert len(saved_files) == 0

    def test_cli_format_explicit_flag(
        self, runner, mock_maigret_collect, mock_filter_passthrough, tmp_output_dir
    ):
        """--format cli is accepted and produces no saved file."""
        result = runner.invoke(
            app, ["search", "--username", "testuser", "--format", "cli"]
        )
        assert result.exit_code == 0
        saved_files = list(tmp_output_dir.glob("*.*"))
        assert len(saved_files) == 0
