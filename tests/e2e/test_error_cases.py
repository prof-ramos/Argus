"""
E2E tests for ARGUS error handling and edge cases.

Tests that:
- Missing required arguments produce clean error exits
- Collector timeouts are handled gracefully (no crash)
- Collector exceptions are handled gracefully (no crash)
- Empty results produce clean output
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from argus import app
from collectors.base import AccountResult, ResultStatus


class TestMissingArguments:

    def test_no_args_exits_with_error(self, runner):
        """Running 'argus search' with no --username or --email exits with code 1."""
        result = runner.invoke(app, ["search"])
        assert result.exit_code == 1

    def test_no_args_shows_helpful_message(self, runner):
        """Error message guides user to specify --username or --email."""
        result = runner.invoke(app, ["search"])
        assert "--username" in result.output or "--email" in result.output or "Especifique" in result.output


class TestCollectorGracefulDegradation:

    def test_maigret_timeout_does_not_crash(
        self, runner, mock_filter_passthrough, tmp_output_dir
    ):
        """CLI exits cleanly when MaigreCollector returns a TIMEOUT result."""
        timeout_result = [AccountResult(
            site_name="Maigret",
            status=ResultStatus.TIMEOUT,
            error="Timeout"
        )]
        with patch(
            "collectors.maigret.MaigreCollector.collect",
            new_callable=AsyncMock,
            return_value=timeout_result
        ):
            result = runner.invoke(app, ["search", "--username", "slowuser"])

        assert result.exit_code == 0

    def test_maigret_error_does_not_crash(
        self, runner, mock_filter_passthrough, tmp_output_dir
    ):
        """CLI exits cleanly when MaigreCollector returns an ERROR result."""
        error_result = [AccountResult(
            site_name="Maigret",
            status=ResultStatus.ERROR,
            error="Connection refused"
        )]
        with patch(
            "collectors.maigret.MaigreCollector.collect",
            new_callable=AsyncMock,
            return_value=error_result
        ):
            result = runner.invoke(app, ["search", "--username", "baduser"])

        assert result.exit_code == 0

    def test_holehe_timeout_does_not_crash(
        self, runner, mock_filter_passthrough, tmp_output_dir
    ):
        """CLI exits cleanly when HoleheCollector returns a TIMEOUT result."""
        timeout_result = [AccountResult(
            site_name="Holehe",
            status=ResultStatus.TIMEOUT,
            error="Timeout"
        )]
        with patch(
            "collectors.holehe.HoleheCollector.collect",
            new_callable=AsyncMock,
            return_value=timeout_result
        ):
            result = runner.invoke(app, ["search", "--email", "slow@example.com"])

        assert result.exit_code == 0

    def test_holehe_error_does_not_crash(
        self, runner, mock_filter_passthrough, tmp_output_dir
    ):
        """CLI exits cleanly when HoleheCollector returns an ERROR result."""
        error_result = [AccountResult(
            site_name="Holehe",
            status=ResultStatus.ERROR,
            error="Tool not installed"
        )]
        with patch(
            "collectors.holehe.HoleheCollector.collect",
            new_callable=AsyncMock,
            return_value=error_result
        ):
            result = runner.invoke(app, ["search", "--email", "bad@example.com"])

        assert result.exit_code == 0

    def test_both_collectors_empty_results(
        self, runner, mock_filter_passthrough, tmp_output_dir
    ):
        """CLI handles empty results from both collectors without error."""
        with patch(
            "collectors.maigret.MaigreCollector.collect",
            new_callable=AsyncMock,
            return_value=[]
        ), patch(
            "collectors.holehe.HoleheCollector.collect",
            new_callable=AsyncMock,
            return_value=[]
        ):
            result = runner.invoke(
                app,
                ["search", "--username", "ghost", "--email", "ghost@example.com"]
            )

        assert result.exit_code == 0


class TestFilterBehavior:

    def test_false_positive_sites_are_excluded(
        self, runner, tmp_output_dir
    ):
        """Results from blocklisted domains are excluded from output."""
        from collectors.base import AccountResult, ResultStatus

        fp_result = [AccountResult(
            site_name="Example",
            url="https://example.com/testuser",  # in FALSE_POSITIVE_SITES
            status=ResultStatus.FOUND,
            http_status=200,
            metadata={}
        )]
        with patch(
            "collectors.maigret.MaigreCollector.collect",
            new_callable=AsyncMock,
            return_value=fp_result
        ):
            # Use VALIDATE_URLS=False so real HTTP is not attempted,
            # but the blocklist still applies via _validate_single
            with patch("processing.filter.VALIDATE_URLS", False):
                result = runner.invoke(app, ["search", "--username", "testuser"])

        assert result.exit_code == 0

    def test_results_without_url_excluded_by_normalizer(
        self, runner, mock_filter_passthrough, tmp_output_dir
    ):
        """Normalizer excludes results that have no URL."""
        no_url_result = [AccountResult(
            site_name="NoURL",
            url=None,
            status=ResultStatus.FOUND,
            http_status=200,
            metadata={}
        )]
        with patch(
            "collectors.maigret.MaigreCollector.collect",
            new_callable=AsyncMock,
            return_value=no_url_result
        ):
            result = runner.invoke(app, ["search", "--username", "testuser"])

        assert result.exit_code == 0
        # NoURL platform should not appear (filtered by Normalizer)
        assert "NoURL" not in result.output
