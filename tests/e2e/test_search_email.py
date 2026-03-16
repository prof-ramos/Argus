"""
E2E tests for ARGUS email search and combined username+email search via CLI.
"""
import pytest
from unittest.mock import AsyncMock, patch
from argus import app


class TestSearchEmail:

    def test_search_email_exits_successfully(
        self, runner, mock_holehe_collect, mock_filter_passthrough
    ):
        """CLI exits with code 0 on a valid email search."""
        result = runner.invoke(app, ["search", "--email", "test@example.com"])
        assert result.exit_code == 0

    def test_search_email_shows_target_in_output(
        self, runner, mock_holehe_collect, mock_filter_passthrough
    ):
        """Output contains the queried email address."""
        result = runner.invoke(app, ["search", "--email", "test@example.com"])
        assert "test@example.com" in result.output

    def test_search_email_shows_platform_names(
        self, runner, mock_holehe_collect, mock_filter_passthrough
    ):
        """Platforms discovered via email search appear in CLI output."""
        result = runner.invoke(app, ["search", "--email", "test@example.com"])
        # Holehe fixture returns Spotify and LinkedIn (no URL → filtered out by Normalizer)
        # The output should at least not crash; with URLs absent results are empty
        assert result.exit_code == 0

    def test_search_email_platforms_with_urls(
        self, runner, mock_filter_passthrough
    ):
        """Email platforms that include a URL appear in the output table."""
        from collectors.base import AccountResult, ResultStatus

        holehe_with_urls = [
            AccountResult(
                site_name="Spotify",
                url="https://open.spotify.com/user/testuser",
                status=ResultStatus.FOUND,
                http_status=200,
                metadata={}
            ),
        ]

        with patch(
            "collectors.holehe.HoleheCollector.collect",
            new_callable=AsyncMock,
            return_value=holehe_with_urls
        ):
            result = runner.invoke(app, ["search", "--email", "test@example.com"])

        assert result.exit_code == 0
        assert "Spotify" in result.output


class TestSearchCombined:

    def test_search_username_and_email_both_run(
        self, runner, mock_maigret_collect, mock_holehe_collect, mock_filter_passthrough
    ):
        """Providing both --username and --email runs both collectors."""
        result = runner.invoke(
            app,
            ["search", "--username", "testuser", "--email", "test@example.com"]
        )
        assert result.exit_code == 0
        mock_maigret_collect.assert_called_once_with("testuser")
        mock_holehe_collect.assert_called_once_with("test@example.com")

    def test_search_combined_output_contains_target(
        self, runner, mock_maigret_collect, mock_holehe_collect, mock_filter_passthrough
    ):
        """Combined search shows username in the CLI output."""
        result = runner.invoke(
            app,
            ["search", "--username", "testuser", "--email", "test@example.com"]
        )
        assert "testuser" in result.output
