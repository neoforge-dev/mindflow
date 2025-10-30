"""
Pytest configuration and shared fixtures.
"""

import os
from typing import Generator

import pytest
from dotenv import load_dotenv

from tests.client import MindFlowClient

load_dotenv()


@pytest.fixture(scope="session")
def api_url() -> str:
    """Get API URL from environment or config."""
    url = os.getenv(
        "DEPLOYMENT_URL",
        "https://script.google.com/macros/s/AKfycbwz_zgYRCztreHox0qpWBQLdo5F174ZE8oiNUb_IcOYjtR3jJho8GHpSlruQaqJ1eJWqQ/exec",
    )
    return url


@pytest.fixture(scope="session")
def client(api_url: str) -> MindFlowClient:
    """Create API client for tests."""
    return MindFlowClient(base_url=api_url)


@pytest.fixture
def task_id_tracker() -> Generator[list[str], None, None]:
    """Track created task IDs for cleanup."""
    task_ids: list[str] = []
    yield task_ids
    # Cleanup would go here if we had a delete endpoint
    # For now, tasks remain in the sheet for inspection


@pytest.fixture
def sample_task_data() -> dict:
    """Sample task data for testing."""
    return {
        "title": "Test Task",
        "description": "This is a test task",
        "priority": 3,
        "due_date": "2025-11-15T17:00:00Z",
    }
