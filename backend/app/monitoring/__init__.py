"""Monitoring and error tracking integration."""

from app.monitoring.sentry import init_sentry

__all__ = ["init_sentry"]
