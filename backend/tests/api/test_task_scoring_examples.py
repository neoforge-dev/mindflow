"""Example test showing actual API response format for documentation."""

import json
from datetime import datetime, timedelta

import pytest


@pytest.mark.asyncio
async def test_best_task_api_response_example(authenticated_client, db_session):
    """Example showing actual API response from /api/tasks/best endpoint.

    This test demonstrates the complete response structure for documentation.
    """
    from app.db.crud import TaskCRUD

    # Create a realistic set of tasks
    overdue_date = datetime.utcnow() - timedelta(hours=12)
    await TaskCRUD.create(
        db_session,
        {
            "title": "Submit quarterly report",
            "description": "Need to send Q4 financial report to stakeholders",
            "priority": 5,
            "due_date": overdue_date,
            "effort_estimate_minutes": 45,
            "status": "pending",
            "user_id": authenticated_client.user_id,
        },
    )

    today_date = datetime.utcnow() + timedelta(hours=8)
    await TaskCRUD.create(
        db_session,
        {
            "title": "Review pull request #42",
            "description": "Code review for authentication refactor",
            "priority": 4,
            "due_date": today_date,
            "effort_estimate_minutes": 20,
            "status": "pending",
            "user_id": authenticated_client.user_id,
        },
    )

    await TaskCRUD.create(
        db_session,
        {
            "title": "Update team wiki",
            "description": "Document new onboarding process",
            "priority": 2,
            "effort_estimate_minutes": 60,
            "status": "pending",
            "user_id": authenticated_client.user_id,
        },
    )

    await TaskCRUD.create(
        db_session,
        {
            "title": "Quick bug fix: typo in button",
            "description": "Fix submit button text typo",
            "priority": 1,
            "effort_estimate_minutes": 5,
            "status": "pending",
            "user_id": authenticated_client.user_id,
        },
    )

    # Call the /best endpoint
    response = await authenticated_client.get("/api/tasks/best")

    assert response.status_code == 200
    data = response.json()

    # Print formatted response for documentation
    print("\n" + "=" * 80)
    print("API ENDPOINT: GET /api/tasks/best")
    print("=" * 80)
    print("\nRESPONSE (200 OK):")
    print(json.dumps(data, indent=2, default=str))
    print("\n" + "=" * 80)

    # Verify structure
    assert "task" in data
    assert "score" in data
    assert "reasoning" in data

    # The overdue, high-priority task should win
    assert data["task"]["title"] == "Submit quarterly report"
    assert "overdue" in data["reasoning"]["recommendation"].lower()

    print(f"\n✓ Best task selected: {data['task']['title']}")
    print(f"✓ Score: {data['score']}")
    print(f"✓ Recommendation: {data['reasoning']['recommendation']}")
    print("=" * 80 + "\n")
