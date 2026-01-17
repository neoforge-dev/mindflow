"""
MindFlow API Client for testing.

Provides a type-safe interface to the MindFlow API endpoints.
"""

import os
from typing import Any, Optional

import requests
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


class APIResponse(BaseModel):
    """Standard API response model."""

    status: str
    code: int
    data: dict[str, Any] | list[dict[str, Any]] | str


class TaskData(BaseModel):
    """Task data model for validation."""

    id: Optional[str] = None
    title: str
    description: Optional[str] = ""
    status: str = "pending"
    priority: int = Field(ge=1, le=5)
    due_date: Optional[str] = None
    snoozed_until: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class MindFlowClient:
    """Client for interacting with MindFlow API."""

    def __init__(self, base_url: Optional[str] = None, timeout: int = 30):
        """
        Initialize the API client.

        Args:
            base_url: Base URL for the API. Defaults to env var DEPLOYMENT_URL.
            timeout: Request timeout in seconds.
        """
        self.base_url = base_url or os.getenv(
            "DEPLOYMENT_URL",
            "https://script.google.com/macros/s/AKfycbwz_zgYRCztreHox0qpWBQLdo5F174ZE8oiNUb_IcOYjtR3jJho8GHpSlruQaqJ1eJWqQ/exec",
        )
        self.timeout = timeout
        self.session = requests.Session()

    def create_task(self, task_data: dict[str, Any]) -> APIResponse:
        """
        Create a new task.

        Args:
            task_data: Task data (title, priority, description, due_date, etc.)

        Returns:
            APIResponse with created task data

        Raises:
            requests.RequestException: On network error or validation error (422)
            requests.HTTPError: On 404 or other HTTP errors
            ValueError: On API error responses (status="error" in body)
        """
        response = self.session.post(
            f"{self.base_url}?action=create",
            json=task_data,
            headers={"Content-Type": "application/json"},
            timeout=self.timeout,
        )
        # Raise exception for HTTP errors (4xx, 5xx)
        if response.status_code >= 400:
            response.raise_for_status()
        
        # Check response body for API-level errors (Google Apps Script returns 200 with error in body)
        response_data = response.json()
        if isinstance(response_data, dict) and response_data.get("status") == "error":
            error_msg = response_data.get("data", {}).get("message", "API error")
            errors = response_data.get("data", {}).get("errors", [])
            if errors:
                error_details = "; ".join([f"{e.get('field', 'unknown')}: {e.get('issue', 'error')}" for e in errors])
                raise ValueError(f"Validation error: {error_details}")
            raise ValueError(f"API error: {error_msg}")
        
        return APIResponse(**response_data)

    def get_best_task(self, timezone: str = "UTC") -> APIResponse:
        """
        Get the best task to work on right now.

        Args:
            timezone: IANA timezone string

        Returns:
            APIResponse with best task data or no_tasks message
        """
        response = self.session.get(
            f"{self.base_url}?action=best&timezone={timezone}", timeout=self.timeout
        )
        response.raise_for_status()
        return APIResponse(**response.json())

    def update_task(self, task_id: str, updates: dict[str, Any]) -> APIResponse:
        """
        Update an existing task.

        Args:
            task_id: Task UUID
            updates: Fields to update

        Returns:
            APIResponse with success confirmation

        Raises:
            requests.HTTPError: On 404 (task not found) or validation error (422)
            ValueError: On API error responses
        """
        response = self.session.post(
            f"{self.base_url}?action=update&id={task_id}",
            json=updates,
            headers={"Content-Type": "application/json"},
            timeout=self.timeout,
        )
        # Raise exception for HTTP errors (4xx, 5xx)
        if response.status_code >= 400:
            response.raise_for_status()
        
        # Check response body for API-level errors
        response_data = response.json()
        if isinstance(response_data, dict) and response_data.get("status") == "error":
            error_msg = response_data.get("data", {}).get("message", "API error")
            raise ValueError(f"API error: {error_msg}")
        
        return APIResponse(**response_data)

    def complete_task(self, task_id: str) -> APIResponse:
        """
        Mark a task as complete.

        Args:
            task_id: Task UUID

        Returns:
            APIResponse with success confirmation

        Raises:
            requests.HTTPError: On 404 (task not found)
            ValueError: On API error responses
        """
        response = self.session.post(
            f"{self.base_url}?action=complete&id={task_id}",
            json={},
            headers={"Content-Type": "application/json"},
            timeout=self.timeout,
        )
        # Raise exception for HTTP errors (4xx, 5xx)
        if response.status_code >= 400:
            response.raise_for_status()
        
        # Check response body for API-level errors
        response_data = response.json()
        if isinstance(response_data, dict) and response_data.get("status") == "error":
            error_msg = response_data.get("data", {}).get("message", "API error")
            raise ValueError(f"API error: {error_msg}")
        
        return APIResponse(**response_data)

    def snooze_task(self, task_id: str, duration: str = "2h") -> APIResponse:
        """
        Snooze a task.

        Args:
            task_id: Task UUID
            duration: Snooze duration (e.g., '2h', '1d', '1w')

        Returns:
            APIResponse with snoozed_until timestamp

        Raises:
            requests.HTTPError: On 404 (task not found)
            ValueError: On API error responses
        """
        response = self.session.post(
            f"{self.base_url}?action=snooze&id={task_id}",
            json={"snooze_duration": duration},
            headers={"Content-Type": "application/json"},
            timeout=self.timeout,
        )
        # Raise exception for HTTP errors (4xx, 5xx)
        if response.status_code >= 400:
            response.raise_for_status()
        
        # Check response body for API-level errors
        response_data = response.json()
        if isinstance(response_data, dict) and response_data.get("status") == "error":
            error_msg = response_data.get("data", {}).get("message", "API error")
            raise ValueError(f"API error: {error_msg}")
        
        return APIResponse(**response_data)

    def query_tasks(
        self,
        status: Optional[str] = None,
        priority: Optional[int] = None,
        limit: int = 50,
    ) -> APIResponse:
        """
        Query tasks with filters.

        Args:
            status: Filter by status
            priority: Filter by priority
            limit: Maximum results

        Returns:
            APIResponse with list of tasks
        """
        params = {"action": "query", "limit": limit}
        if status:
            params["status"] = status
        if priority:
            params["priority"] = priority

        response = self.session.get(
            self.base_url, params=params, timeout=self.timeout
        )
        response.raise_for_status()
        return APIResponse(**response.json())

    def health_check(self) -> bool:
        """
        Check if API is accessible.

        Returns:
            True if API responds, False otherwise
        """
        try:
            response = self.get_best_task()
            return response.status == "success"
        except Exception:
            return False
