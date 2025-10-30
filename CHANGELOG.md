# Changelog

All notable changes to MindFlow will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2025-10-30

### Added
- Custom GPT-optimized OpenAPI schema (`openapi-schema-gpt.json`)
  - 6 clearly separated operations (getBestTask, queryTasks, createTask, updateTask, completeTask, snoozeTask)
  - Response size limits (default 10, max 20 tasks) to prevent ResponseTooLargeError
  - Embedded deployment URL for easier setup
  - Comprehensive validation constraints (additionalProperties, minProperties, required arrays)
- Complete Custom GPT setup guide (`CUSTOM_GPT_SETUP.md`)
  - Quick update instructions
  - Fresh setup walkthrough
  - Troubleshooting section for common issues
  - Schema differences documentation
- Factory-based test data generation (`tests/factories.py`)
  - 15+ specialized factory classes (UrgentTask, OverdueTask, SnoozedTask, etc.)
  - Edge case factories (MaxLengthTitle, Unicode, SpecialCharacters)
  - Pre-configured test data sets (realistic_mixed_tasks, edge_cases, scoring_test_set)
- Comprehensive test suite (60+ tests)
  - API endpoint tests with full coverage
  - Edge case tests (boundaries, unicode, timing, concurrency)
  - Type-safe API client with Pydantic validation
- Modern Python tooling migration
  - Replaced `requirements.txt` with `pyproject.toml`
  - Integrated `uv` package manager for fast dependency management
  - Added `Makefile` with convenient command shortcuts
  - Created comprehensive `UV_GUIDE.md` reference
- Seed data script with Rich UI (`tests/seed_data.py`)
  - Generates 47 realistic tasks covering all scenarios
  - Beautiful progress visualization
  - Summary statistics and recommendations
- Updated documentation
  - Fixed all commands to use `uv run` prefix
  - Clarified which OpenAPI schema to use for different purposes
  - Updated setup instructions to reflect modern tooling

### Changed
- Migrated from `requirements.txt` to `pyproject.toml` for Python packaging
- Updated all test commands to use `uv run` prefix
- Reduced default query limit from 50 to 10 tasks (max 20)
- Separated combined API operations into distinct endpoints
- Improved OpenAPI schema validation and compliance

### Fixed
- OpenAPI schema validation error: "object schema missing properties"
  - Added explicit empty properties with additionalProperties constraint to completeTask endpoint
  - Applied proper validation to all request/response schemas
- Factory Boy Faker usage bug
  - Fixed `OverdueTaskFactory.title` LazyAttribute to use correct Faker syntax
- ResponseTooLargeError in Custom GPT queries
  - Added response size limits to prevent overwhelming responses
  - Documented filtering best practices
- Missing `uv run` prefixes in TESTING.md
- Query limit documentation inconsistency in README.md
- Schema file reference ambiguity

### Documentation
- Added `CHANGELOG.md` to track project evolution
- Added `CUSTOM_GPT_SETUP.md` with comprehensive setup guide
- Added `UV_GUIDE.md` with modern Python tooling reference
- Updated `README.md` to reflect current architecture and tooling
- Updated `TESTING.md` with correct command syntax
- Added clarification about which OpenAPI schema to use

## [0.2.0] - 2025-10-30

### Added
- Complete API implementation in Google Apps Script
  - Create, read, update, delete operations
  - Relevance scoring algorithm
  - Audit logging to separate sheet
- Original OpenAPI schema (`openapi-schema.json`)
- Initial documentation
  - `README.md` with architecture overview
  - `DEPLOYMENT.md` with manual setup instructions
  - `AUTOMATED_SETUP.md` with bash automation scripts
  - Implementation guides in `docs/raw/`
- Basic test infrastructure
  - Setup scripts (bash, npm)
  - Initial test files

## [0.1.0] - 2025-10-29

### Added
- Project initialization
- Core architecture design
  - Custom GPT → Google Apps Script → Google Sheets
  - Deterministic relevance scoring model
- Initial documentation
  - Architecture one-pager
  - Task manager guide
  - Project requirements

---

## Version History

- **0.3.0** - Modern tooling, comprehensive testing, GPT-optimized schema
- **0.2.0** - Complete API implementation, documentation
- **0.1.0** - Initial architecture and design

---

## Upgrade Guide

### From 0.2.0 to 0.3.0

**Python Dependencies:**
```bash
# Remove old requirements.txt approach
rm requirements.txt

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies
uv sync --all-extras
```

**Custom GPT Update:**
1. Open your Custom GPT configuration
2. Go to Actions section
3. Import `src/gas/openapi-schema-gpt.json` (new file)
4. Verify all 6 operations are visible
5. Test with "What should I do next?"

**Testing:**
```bash
# Seed test data
make seed

# Run tests
make test
```

See [CUSTOM_GPT_SETUP.md](./CUSTOM_GPT_SETUP.md) for detailed upgrade instructions.

---

## Contributing

When adding entries to this changelog:
1. Use the format: `### [Added|Changed|Deprecated|Removed|Fixed|Security]`
2. Include file references and line numbers where applicable
3. Explain both what changed and why it matters
4. Link to related documentation

---

[Unreleased]: https://github.com/mindflow/mindflow/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/mindflow/mindflow/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/mindflow/mindflow/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/mindflow/mindflow/releases/tag/v0.1.0
