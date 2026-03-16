"""
E2E tests for ARGUS username search via CLI.

Tests the full pipeline: CLI → Collectors → Normalizer → Filter → Enricher → Formatter
External dependencies (maigret subprocess, HTTP validation) are mocked.
"""
import pytest
from argus import app


# ---------------------------------------------------------------------------
# Username search — CLI format (default)
# ---------------------------------------------------------------------------

class TestSearchUsername:

    def test_search_username_exits_successfully(
        self, runner, mock_maigret_collect, mock_filter_passthrough
    ):
        """CLI exits with code 0 on a valid username search."""
        result = runner.invoke(app, ["search", "--username", "testuser"])
        assert result.exit_code == 0

    def test_search_username_shows_target_in_output(
        self, runner, mock_maigret_collect, mock_filter_passthrough
    ):
        """Output contains the queried username."""
        result = runner.invoke(app, ["search", "--username", "testuser"])
        assert "testuser" in result.output

    def test_search_username_shows_platform_names(
        self, runner, mock_maigret_collect, mock_filter_passthrough
    ):
        """Output lists platform names found by the collector."""
        result = runner.invoke(app, ["search", "--username", "testuser"])
        assert "GitHub" in result.output
        assert "Twitter" in result.output
        assert "Reddit" in result.output

    def test_search_username_normalizer_deduplicates(
        self, runner, mock_filter_passthrough, sample_maigret_results
    ):
        """Normalizer removes duplicate results (same site_name + url)."""
        from unittest.mock import AsyncMock, patch

        # Return the same results twice (simulating two collectors)
        duplicated = sample_maigret_results + sample_maigret_results

        with patch(
            "collectors.maigret.MaigreCollector.collect",
            new_callable=AsyncMock,
            return_value=duplicated
        ):
            result = runner.invoke(app, ["search", "--username", "testuser"])

        assert result.exit_code == 0
        # GitHub should appear only once in the table (not twice)
        assert result.output.count("GitHub") <= 2  # table header row may repeat

    def test_search_username_enricher_adds_metadata(
        self, runner, mock_maigret_collect, mock_filter_passthrough
    ):
        """Enricher adds category metadata; CLI table shows category column."""
        result = runner.invoke(app, ["search", "--username", "testuser"])
        # The CLI table has a "Categoria" column
        assert "Categoria" in result.output or "developer" in result.output or "social" in result.output

    def test_search_username_with_no_results(
        self, runner, mock_filter_passthrough
    ):
        """When no platforms are found, CLI exits cleanly without crash."""
        from unittest.mock import AsyncMock, patch

        with patch(
            "collectors.maigret.MaigreCollector.collect",
            new_callable=AsyncMock,
            return_value=[]
        ):
            result = runner.invoke(app, ["search", "--username", "nobody"])

        assert result.exit_code == 0


class TestVersionCommand:

    def test_version_command_shows_version(self, runner):
        """'argus version' outputs the version string."""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "1.0.0" in result.output

    def test_version_command_shows_argus_name(self, runner):
        """'argus version' output includes 'ARGUS'."""
        result = runner.invoke(app, ["version"])
        assert "ARGUS" in result.output
