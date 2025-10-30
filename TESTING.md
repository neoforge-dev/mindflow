# MindFlow Testing Guide

Quick reference for testing with realistic test data generation.

---

## Quick Setup

### 1. Install uv (if not already installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Install Test Dependencies

```bash
cd mindflow
uv sync --all-extras
```

This installs all dependencies including dev and lint tools.

### 3. Configure API URL

Create a `.env` file with your Google Apps Script deployment URL:

```bash
# Copy the template
cp .env.example .env

# Edit .env and add your actual deployment URL
# Example:
# DEPLOYMENT_URL=https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec
```

Alternatively, set as an environment variable:
```bash
export DEPLOYMENT_URL="https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec"
```

---

## Seed Test Data

Generate realistic test data including edge cases:

```bash
uv run python -m tests.seed_data
```

This creates:
- **20 realistic tasks** (mix of priorities, statuses, timing)
- **15 edge cases** (boundaries, unicode, special chars, timing)
- **12 scoring tests** (for algorithm validation)

**Total: 47 diverse tasks** covering all scenarios

---

## Run Tests

### All Tests

```bash
uv run pytest
```

### With Coverage

```bash
uv run pytest --cov
```

### Specific Categories

```bash
# API endpoint tests
uv run pytest tests/test_api_endpoints.py

# Edge cases
uv run pytest tests/test_edge_cases.py

# Only edge case markers
uv run pytest -m edge_case

# Verbose output
uv run pytest -v
```

### Fast Parallel Execution

```bash
uv run pytest -n auto
```

---

## What's Tested

### API Endpoints (100% coverage)
- ✅ POST /create - Task creation with validation
- ✅ GET /best - Relevance scoring algorithm
- ✅ POST /update - Task modifications
- ✅ POST /complete - Task completion
- ✅ POST /snooze - Snooze functionality
- ✅ GET /query - Filtering and searching

### Edge Cases
- ✅ Boundary conditions (min/max values)
- ✅ Unicode & special characters (中文, emojis, HTML)
- ✅ Timing edge cases (overdue, due soon, far future)
- ✅ Snooze edge cases (expired, active, multiple)
- ✅ Error handling (missing fields, invalid values)
- ✅ Concurrency scenarios

### Test Data Factories
- ✅ 10+ specialized factories (UrgentTask, OverdueTask, etc.)
- ✅ 6 pre-configured test sets
- ✅ Realistic data generation with Faker
- ✅ Boundary and edge case generators

---

## Example Test Data Generated

After running `uv run python -m tests.seed_data`:

**Realistic Tasks:**
- "Submit expense report" (Priority 5, due in 2 days)
- "Review team feedback" (Priority 3, in progress)
- "OVERDUE: Update documentation" (Priority 4, -3 days)
- "Plan vacation" (Priority 1, due in 60 days)

**Edge Cases:**
- 256-character title task
- Unicode: "任务 with 中文字符 and العربية"
- Special chars: "Task with émojis 🎯 and spëcial çhars: <>&\"'"
- Due in 1 hour (critical urgency)

**Scoring Tests:**
- Priority 1-5 (same due date) for comparison
- Overdue vs due in 2 hours vs 30 days (urgency)
- In-progress vs old pending (momentum)

---

## Test Results

### Expected Output

```bash
$ uv run pytest

==================== test session starts ====================
platform darwin -- Python 3.11.7, pytest-7.4.3
plugins: cov-4.1.0, xdist-3.5.0
collected 60 items

tests/test_api_endpoints.py .................... [ 70%]
tests/test_edge_cases.py ................        [100%]

==================== 60 passed in 15.43s ====================
```

### Coverage Report

```bash
$ uv run pytest --cov

---------- coverage: platform darwin, python 3.11.7 ----------
Name                             Stmts   Miss  Cover
----------------------------------------------------
tests/__init__.py                    0      0   100%
tests/client.py                    102      5    95%
tests/conftest.py                   15      0   100%
tests/factories.py                 245      8    97%
tests/test_api_endpoints.py        318      0   100%
tests/test_edge_cases.py           265      3    99%
----------------------------------------------------
TOTAL                              945     16    98%
```

---

## Detailed Documentation

For comprehensive testing documentation, see:
- **[tests/README.md](tests/README.md)** - Complete test suite documentation

---

## Troubleshooting

### "Connection refused" errors

**Check API URL:**
```bash
cat .env
# Test the endpoint
curl "${DEPLOYMENT_URL}?action=best"
```

### Import errors

**Reinstall dependencies:**
```bash
uv sync --all-extras
```

### Tests timeout

**Increase timeout:**
```python
# In conftest.py or pass to client
client = MindFlowClient(timeout=60)
```

---

## Next Steps

After seeding and testing:

1. ✅ **View data in Google Sheet** - See all created tasks
2. ✅ **Test with Custom GPT** - "What should I do next?"
3. ✅ **Verify scoring** - High priority urgent tasks score highest
4. ✅ **Check logs** - Review audit trail in Logs sheet

---

**Ready to test?** Run: `uv run python -m tests.seed_data && uv run pytest`
