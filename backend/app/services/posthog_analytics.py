"""PostHog analytics service for MindFlow."""

import logging
from typing import Any

try:
    import posthog

    HAS_POSTHOG = True
except ImportError:
    HAS_POSTHOG = False

from app.config import settings

logger = logging.getLogger(__name__)


class PostHogAnalytics:
    """PostHog analytics client for MindFlow events."""

    _initialized = False

    @classmethod
    def initialize(cls) -> None:
        """Initialize PostHog client."""
        if cls._initialized:
            return

        if not HAS_POSTHOG:
            logger.warning("PostHog package not installed - analytics disabled")
            return

        api_key = settings.posthog_api_key
        host = settings.posthog_host

        if not api_key:
            logger.warning("PostHog API key not configured - analytics disabled")
            return

        posthog.project_api_key = api_key
        posthog.host = host
        posthog.debug = settings.debug
        cls._initialized = True
        logger.info("PostHog analytics initialized")

    @classmethod
    def capture(
        cls,
        user_id: str,
        event: str,
        properties: dict[str, Any] | None = None,
    ) -> None:
        """Capture an analytics event."""
        if not cls._initialized:
            cls.initialize()

        if not cls._initialized or not HAS_POSTHOG:
            return

        try:
            posthog.capture(
                distinct_id=user_id,
                event=event,
                properties={
                    "product": "mindflow",
                    **(properties or {}),
                },
            )
        except Exception as e:
            logger.error(f"PostHog capture failed: {e}")

    @classmethod
    def identify(
        cls,
        user_id: str,
        properties: dict[str, Any] | None = None,
    ) -> None:
        """Identify a user with properties."""
        if not cls._initialized:
            cls.initialize()

        if not cls._initialized or not HAS_POSTHOG:
            return

        try:
            posthog.identify(user_id, properties or {})
        except Exception as e:
            logger.error(f"PostHog identify failed: {e}")

    # MindFlow-specific events
    @classmethod
    def task_created(
        cls,
        user_id: str,
        task_id: str,
        priority: str | None = None,
    ) -> None:
        """Track task creation."""
        cls.capture(
            user_id=user_id,
            event="mf_task_created",
            properties={
                "task_id": task_id,
                "priority": priority,
            },
        )

    @classmethod
    def task_completed(
        cls,
        user_id: str,
        task_id: str,
    ) -> None:
        """Track task completion."""
        cls.capture(
            user_id=user_id,
            event="mf_task_completed",
            properties={
                "task_id": task_id,
            },
        )

    @classmethod
    def gpt_action(
        cls,
        user_id: str,
        action: str,
        task_count: int = 0,
    ) -> None:
        """Track GPT action (ChatGPT interaction)."""
        cls.capture(
            user_id=user_id,
            event="mf_gpt_action",
            properties={
                "action": action,
                "task_count": task_count,
            },
        )

    @classmethod
    def project_created(
        cls,
        user_id: str,
        project_id: str,
    ) -> None:
        """Track project creation."""
        cls.capture(
            user_id=user_id,
            event="mf_project_created",
            properties={
                "project_id": project_id,
            },
        )

    @classmethod
    def focus_session_started(
        cls,
        user_id: str,
        duration_minutes: int,
    ) -> None:
        """Track focus session start."""
        cls.capture(
            user_id=user_id,
            event="mf_focus_session_started",
            properties={
                "duration_minutes": duration_minutes,
            },
        )
