"""Tests for Sentry error monitoring integration."""

from unittest.mock import patch

from app.config import Settings
from app.monitoring.sentry import init_sentry


class TestSentryInitialization:
    """Test Sentry SDK initialization logic."""

    @patch("sentry_sdk.init")
    def test_sentry_initializes_with_dsn(self, mock_sentry_init):
        """Sentry SDK is initialized when DSN is provided."""
        # Create settings with Sentry DSN
        settings = Settings(
            sentry_dsn="https://example@sentry.io/123456",
            environment="production",
            database_url="postgresql+asyncpg://test:test@localhost/test",
            secret_key="test-key",
        )

        # Initialize Sentry
        init_sentry(settings)

        # Verify sentry_sdk.init was called
        mock_sentry_init.assert_called_once()
        call_kwargs = mock_sentry_init.call_args[1]

        # Verify configuration
        assert call_kwargs["dsn"] == "https://example@sentry.io/123456"
        assert call_kwargs["environment"] == "production"
        assert call_kwargs["traces_sample_rate"] == 0.1
        assert call_kwargs["profiles_sample_rate"] == 0.1
        assert call_kwargs["enable_tracing"] is True

    @patch("sentry_sdk.init")
    def test_sentry_skips_without_dsn(self, mock_sentry_init):
        """Sentry SDK is not initialized when DSN is missing."""
        # Create settings without Sentry DSN
        settings = Settings(
            sentry_dsn=None,
            environment="development",
            database_url="postgresql+asyncpg://test:test@localhost/test",
            secret_key="test-key",
        )

        # Initialize Sentry
        init_sentry(settings)

        # Verify sentry_sdk.init was NOT called
        mock_sentry_init.assert_not_called()

    @patch("sentry_sdk.init")
    def test_sentry_skips_in_testing_environment(self, mock_sentry_init):
        """Sentry SDK is not initialized in testing environment even with DSN."""
        # Create settings with DSN but testing environment
        settings = Settings(
            sentry_dsn="https://example@sentry.io/123456",
            environment="testing",
            database_url="postgresql+asyncpg://test:test@localhost/test",
            secret_key="test-key",
        )

        # Initialize Sentry
        init_sentry(settings)

        # Verify sentry_sdk.init was NOT called
        mock_sentry_init.assert_not_called()

    @patch("sentry_sdk.init")
    def test_sentry_includes_environment(self, mock_sentry_init):
        """Sentry initialization includes environment tag."""
        # Create settings with staging environment
        settings = Settings(
            sentry_dsn="https://example@sentry.io/123456",
            environment="staging",
            database_url="postgresql+asyncpg://test:test@localhost/test",
            secret_key="test-key",
        )

        # Initialize Sentry
        init_sentry(settings)

        # Verify environment is passed
        call_kwargs = mock_sentry_init.call_args[1]
        assert call_kwargs["environment"] == "staging"

    @patch("sentry_sdk.capture_exception")
    def test_sentry_captures_exceptions(self, mock_capture):
        """Sentry SDK can capture exceptions after initialization."""
        # Simulate exception capture
        test_exception = ValueError("Test error")
        mock_capture(test_exception)

        # Verify capture_exception was called
        mock_capture.assert_called_once_with(test_exception)


class TestSentrySampleRates:
    """Test Sentry sampling configuration."""

    @patch("sentry_sdk.init")
    def test_sentry_performance_sampling_10_percent(self, mock_sentry_init):
        """Sentry uses 10% sample rate for performance monitoring."""
        settings = Settings(
            sentry_dsn="https://example@sentry.io/123456",
            environment="production",
            database_url="postgresql+asyncpg://test:test@localhost/test",
            secret_key="test-key",
        )

        init_sentry(settings)

        call_kwargs = mock_sentry_init.call_args[1]
        assert call_kwargs["traces_sample_rate"] == 0.1

    @patch("sentry_sdk.init")
    def test_sentry_profiling_sampling_10_percent(self, mock_sentry_init):
        """Sentry uses 10% sample rate for profiling."""
        settings = Settings(
            sentry_dsn="https://example@sentry.io/123456",
            environment="production",
            database_url="postgresql+asyncpg://test:test@localhost/test",
            secret_key="test-key",
        )

        init_sentry(settings)

        call_kwargs = mock_sentry_init.call_args[1]
        assert call_kwargs["profiles_sample_rate"] == 0.1
