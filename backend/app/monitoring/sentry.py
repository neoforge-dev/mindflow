"""Sentry error monitoring integration.

Provides centralized error tracking and performance monitoring
for production environments. Sentry is optional and only
initialized if SENTRY_DSN is configured.
"""

from app.config import Settings


def init_sentry(app_settings: Settings) -> None:
    """Initialize Sentry SDK if DSN is configured.

    Args:
        app_settings: Application settings containing optional SENTRY_DSN

    Configuration:
        - SENTRY_DSN: Sentry project DSN (Data Source Name)
        - ENVIRONMENT: Used to tag errors by environment
        - traces_sample_rate: 10% of transactions sent for performance monitoring
        - profiles_sample_rate: 10% of transactions profiled for performance insights

    Note:
        Sentry is disabled in testing environments to avoid noise.
    """
    if not app_settings.sentry_dsn or app_settings.is_testing:
        return

    import sentry_sdk

    sentry_sdk.init(
        dsn=app_settings.sentry_dsn,
        environment=app_settings.environment,
        traces_sample_rate=0.1,  # 10% of requests for performance monitoring
        profiles_sample_rate=0.1,  # 10% of requests for profiling
        enable_tracing=True,
    )
