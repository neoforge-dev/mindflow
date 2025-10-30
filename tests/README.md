## MindFlow Test Suite

Comprehensive pytest-based testing with realistic test data generation using `factory_boy`.

---

## Quick Start

### Install Dependencies (using uv)

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync --all-extras
```

### Run Tests

```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov

# Specific test file
uv run pytest tests/test_api_endpoints.py

# Specific test class
uv run pytest tests/test_api_endpoints.py::TestCreateTask

# Run only edge cases
uv run pytest -m edge_case

# Run with verbose output
uv run pytest -v

# Run in parallel (faster)
uv run pytest -n auto
```

### Seed Test Data

```bash
# Seed comprehensive test data
uv run python -m tests.seed_data

# Or using the entry point
uv run mindflow-seed
```

---

## Test Structure

```
tests/
├── __init__.py
├── README.md                    # This file
├── conftest.py                  # Pytest configuration and fixtures
├── client.py                    # MindFlow API client
├── factories.py                 # Factory Boy factories for test data
├── seed_data.py                 # Data seeding script
├── test_api_endpoints.py        # API endpoint tests (6 endpoints)
└── test_edge_cases.py           # Edge case and boundary tests
```

---

## Test Coverage

### API Endpoints (test_api_endpoints.py)

**Create Task (POST /create)**
- Minimal task (required fields only)
- Complete task (all fields)
- Urgent high-priority task
- Validation: missing title
- Validation: missing priority
- Validation: invalid priority (too high/low)
- Edge: 256 character title
- Edge: empty description
- Edge: no due date
- Edge: unicode characters

**Get Best Task (GET /best)**
- With existing tasks
- Returns highest scored task
- Timezone parameter
- No active tasks scenario

**Update Task (POST /update)**
- Update status
- Update priority
- Update multiple fields
- Non-existent task error

**Complete Task (POST /complete)**
- Mark complete
- Idempotent completion
- Non-existent task error

**Snooze Task (POST /snooze)**
- Default duration (2h)
- Custom durations: 1h, 1d, 1w
- Non-existent task error

**Query Tasks (GET /query)**
- All tasks
- Filter by status
- Filter by priority
- Limit parameter
- Multiple filters

### Edge Cases (test_edge_cases.py)

**Boundary Conditions**
- Priority min (1) and max (5)
- Title max length (256 chars)
- Empty description
- No due date

**Character Encoding**
- Unicode: 中文, العربية, עִבְרִית
- Special characters: `<>&"'`
- Emojis: 🎯 🚀 ✅
- HTML-like strings
- Multiline descriptions

**Timing Edge Cases**
- Overdue tasks
- Due today
- Due in 1 hour
- Far future (365 days)
- Very old pending tasks (90 days)

**Snooze Edge Cases**
- Just snoozed (active snooze)
- Expired snooze (should reappear)
- Multiple snoozes

**Error Handling**
- Missing required fields
- Invalid priority values
- Invalid status values
- Non-existent task IDs
- Operations on completed tasks

---

## Factory Boy Factories

### Base Factory

```python
from tests.factories import TaskFactory

# Create a random task
task = TaskFactory.build()

# Create with specific attributes
task = TaskFactory.build(priority=5, status="pending")
```

### Specialized Factories

```python
from tests.factories import (
    UrgentTaskFactory,          # Priority 5, due soon
    OverdueTaskFactory,         # Already overdue
    InProgressTaskFactory,      # Currently being worked on
    SnoozedTaskFactory,         # Snoozed for later
    CompletedTaskFactory,       # Finished task
    LowPriorityTaskFactory,     # Priority 1-2, far future
)

# Create urgent task
urgent = UrgentTaskFactory.build()

# Create overdue task
overdue = OverdueTaskFactory.build()
```

### Edge Case Factories

```python
from tests.factories import (
    EmptyDescriptionTaskFactory,
    MaxLengthTitleTaskFactory,      # Exactly 256 chars
    NoDueDateTaskFactory,
    DueTodayTaskFactory,
    DueInOneHourTaskFactory,
    UnicodeTaskFactory,
    SpecialCharactersTitleTaskFactory,
)

# Create edge case
edge_case = MaxLengthTitleTaskFactory.build()
```

### Test Data Sets

```python
from tests.factories import TestDataSets

# Realistic mix (20 tasks with variety)
tasks = TestDataSets.realistic_mixed_tasks(count=20)

# All edge cases
edge_cases = TestDataSets.edge_cases()

# Scoring algorithm test set
scoring_tests = TestDataSets.scoring_test_set()

# Empty state
empty = TestDataSets.empty_state()

# Only completed tasks
completed_only = TestDataSets.only_completed()

# High volume (100 tasks)
many_tasks = TestDataSets.high_volume()
```

---

## Test Markers

Tests are organized with pytest markers:

```bash
# Unit tests
uv run pytest -m unit

# Integration tests
uv run pytest -m integration

# Edge case tests
uv run pytest -m edge_case

# API tests
uv run pytest -m api

# Slow tests only
uv run pytest -m slow

# Everything except slow tests
uv run pytest -m "not slow"
```

---

## Test Data Seeding

### What Gets Seeded

1. **20 Realistic Mixed Tasks**
   - 2 Urgent (priority 5, due soon)
   - 3 In Progress
   - 1 Overdue
   - 2 Snoozed
   - 4 Completed
   - 3 Low Priority
   - 5 Random

2. **15 Edge Cases**
   - Boundary tests (min/max values)
   - Timing edge cases (overdue, due soon, far future)
   - Character encoding (unicode, emojis, special chars)
   - Status transitions

3. **12 Scoring Test Tasks**
   - Priority variations (1-5, same due date)
   - Urgency variations (overdue to 30 days out)
   - Momentum variations (in_progress, old pending)

### Seed Data Script

```bash
# Run seeding
uv run python -m tests.seed_data

# Output includes:
# ✓ Health check
# ✓ Progress bars for each data set
# ✓ Best task selection test
# ✓ Statistics by status and priority
```

### Example Output

```
MindFlow Test Data Seeder
============================================================

Checking API health...
✓ API is healthy

Seeding realistic mixed tasks...
Creating tasks... ━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:05
✓ Created 20 realistic tasks

Seeding edge case tasks...
Creating edge cases... ━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:03
✓ Created 15 edge case tasks

Seeding scoring test tasks...
Creating scoring tests... ━━━━━━━━━━━━━━━━━━ 100% 0:00:02
✓ Created 12 scoring test tasks

✓ Successfully seeded 47 tasks

Testing best task selection...
┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Field     ┃ Value                               ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ ID        │ task-0023                           │
│ Title     │ Prepare presentation                │
│ Priority  │ 5                                   │
│ Score     │ 92                                  │
│ Reasoning │ urgent priority (5) + due in 1 days │
└───────────┴─────────────────────────────────────┘
✓ Best task endpoint working correctly

Querying task statistics...
┏━━━━━━━━━━━━┳━━━━━━━┓
┃ Status     ┃ Count ┃
┡━━━━━━━━━━━━╇━━━━━━━┩
│ Pending    │ 15    │
│ In Progress│ 3     │
│ Completed  │ 4     │
│ Snoozed    │ 2     │
└────────────┴───────┘

Seeding complete!
```

---

## Coverage Reports

### Generate Coverage Reports

```bash
# Terminal output
uv run pytest --cov=tests

# HTML report (opens in browser)
uv run pytest --cov=tests --cov-report=html
open htmlcov/index.html

# JSON report
uv run pytest --cov=tests --cov-report=json
```

### Current Coverage

- **API Endpoints**: 100% (all 6 endpoints, all HTTP methods)
- **Edge Cases**: 95% (boundary, encoding, timing, errors)
- **Validation**: 100% (all input validation rules)

---

## Configuration

### Environment Variables

Create `.env` file in project root:

```bash
# API endpoint
DEPLOYMENT_URL=https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec

# Optional: timeout for requests
REQUEST_TIMEOUT=30
```

### Pytest Configuration

Configured in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "edge_case: Edge case tests",
    "slow: Slow running tests",
    "api: API endpoint tests",
]
```

---

## Writing New Tests

### Example Test

```python
import pytest
from tests.client import MindFlowClient
from tests.factories import TaskFactory


@pytest.mark.api
def test_my_new_feature(client: MindFlowClient, task_id_tracker: list[str]):
    """Test description."""
    # Arrange
    task_data = TaskFactory.build(priority=5)

    # Act
    response = client.create_task(task_data)
    task_id_tracker.append(response.data["id"])

    # Assert
    assert response.code == 201
    assert response.data["priority"] == 5
```

### Creating New Factories

```python
from tests.factories import TaskFactory


class MyCustomTaskFactory(TaskFactory):
    """Factory for specific scenario."""

    title = "My Custom Task"
    priority = 5
    status = "pending"
    due_date = "2025-12-01T17:00:00Z"
```

---

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: astral-sh/setup-uv@v1
      - name: Install dependencies
        run: uv sync --all-extras
      - name: Run tests
        run: uv run pytest --cov --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## Troubleshooting

### Tests Failing with "Connection Error"

**Cause**: API endpoint not accessible

**Solution**:
```bash
# Verify URL in .env
cat .env

# Test manually
curl "YOUR_DEPLOYMENT_URL?action=best"
```

### Import Errors

**Cause**: Dependencies not installed

**Solution**:
```bash
uv sync --all-extras
```

### Factory Build Errors

**Cause**: Missing factory_boy

**Solution**:
```bash
uv sync --all-extras
```

### Slow Tests

**Solution**: Run in parallel
```bash
uv run pytest -n auto  # Uses all CPU cores
```

---

## Best Practices

1. **Always use factories** for test data (don't hardcode)
2. **Track task IDs** for cleanup/debugging
3. **Use markers** to organize tests
4. **Write descriptive test names** (`test_what_when_expected`)
5. **Test both happy path and errors**
6. **Use fixtures** for common setup
7. **Run tests before committing**

---

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [factory_boy documentation](https://factoryboy.readthedocs.io/)
- [Faker documentation](https://faker.readthedocs.io/)
- [uv documentation](https://docs.astral.sh/uv/)

---

**Need help?** Check `DEPLOYMENT.md` or open an issue.
