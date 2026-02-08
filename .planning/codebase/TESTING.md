# Testing Patterns

**Analysis Date:** 2026-02-07

## Test Framework

**Runner:**
- pytest 8.0.0+
- Config: `pyproject.toml`
- Test discovery: `testpaths = ["tests"]`
- Python path: `pythonpath = ["src"]` (allows `from particle.core import ...` in tests)

**Assertion Library:**
- pytest's built-in assertions (no additional library)
- Simple assert statements: `assert config.client_id == "test-client"`
- Membership checks: `assert name in core.__all__`

**Run Commands:**
```bash
# Run all tests
pytest

# Watch mode (requires pytest-watch, not in dependencies yet)
# Not detected - would need: pytest-watch

# Coverage (pytest-cov not in optional dependencies)
# Not detected in pyproject.toml
# Would need: pytest-cov

# Run specific test file
pytest tests/test_core_integration.py

# Run specific test class
pytest tests/test_core_integration.py::TestConfig

# Run specific test method
pytest tests/test_core_integration.py::TestConfig::test_config_loads_from_env
```

**Dependencies:**
```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "ruff>=0.1.0",
]
```

## Test File Organization

**Location:**
- Co-located with source: `tests/test_core_integration.py` tests modules in `src/particle/core/`
- Pattern: `tests/test_<module_name>.py` or `tests/test_<domain>_integration.py`

**Naming:**
- Test file: `test_core_integration.py` (integration tests for core infrastructure)
- Test class: `TestConfig`, `TestExceptions`, `TestLogging`, `TestAuth`, `TestHTTPClient`, `TestExports`
- Test method: `test_config_loads_from_env`, `test_secret_str_protects_secret`, etc.

**Structure:**
```
tests/
├── test_core_integration.py    # Integration tests for core/
├── __init__.py
└── (no conftest.py yet - fixtures inline)
```

## Test Structure

**Suite Organization:**
```python
class TestConfig:
    """Tests for ParticleSettings configuration."""

    def test_config_loads_from_env(self):
        """Verify config loads from PARTICLE_* env vars."""
        # Arrange (implicit via fixture)
        # Act
        config = ParticleSettings()
        # Assert
        assert config.client_id == "test-client"

class TestExceptions:
    """Tests for custom exception hierarchy."""

    def test_all_exceptions_inherit_from_base(self):
        """Verify all exceptions inherit from ParticleError."""
        exceptions = [
            ParticleAuthError(),
            ParticleAPIError("test", 500),
            # ... instantiate all types
        ]
        for exc in exceptions:
            assert isinstance(exc, ParticleError)
```

**Patterns:**

**Setup:**
- Fixture: `setup_env` with `monkeypatch` (pytest fixture) sets required env vars
- Autouse: `@pytest.fixture(autouse=True)` runs before every test in module
- All tests can rely on `PARTICLE_CLIENT_ID`, `PARTICLE_CLIENT_SECRET`, `PARTICLE_SCOPE_ID` being set

```python
@pytest.fixture(autouse=True)
def setup_env(monkeypatch):
    """Set up environment variables for all tests."""
    monkeypatch.setenv("PARTICLE_CLIENT_ID", "test-client")
    monkeypatch.setenv("PARTICLE_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("PARTICLE_SCOPE_ID", "test-scope")
```

**Teardown:**
- Not explicit; context managers handle cleanup
- Example: `with ParticleHTTPClient(config) as client:` ensures close() called

**Assertion Pattern:**
- Single assertion per test intent (loosely - may have 2-3 related assertions)
- Assertion messages sometimes implicit, sometimes explicit via third parameter
- Example assertion:
  ```python
  assert config.client_id == "test-client"
  assert config.timeout == 30.0
  ```

## Mocking

**Framework:** unittest.mock (not explicitly imported, but can be used via pytest)

**Actual approach in codebase:** Minimal mocking

**Pattern from actual tests:**
- Pydantic model instantiation used directly (not mocked)
- Real configuration objects created (not mocked)
- Settings loaded from actual environment variables set by fixture
- No external HTTP mocking detected; tests verify local behavior only

**What to Mock (from patterns observed):**
- Private methods when testing public interface (e.g., TokenManager internals)
- External HTTP calls (would use `unittest.mock` or `httpx_mock` if testing ParticleHTTPClient directly)
- Time-based functions if testing timeout behavior (use `freezegun` or mock `datetime`)

**What NOT to Mock:**
- Pydantic models - instantiate directly with test data
- Exception classes - instantiate real exceptions to verify attributes
- Local state management (TokenManager, ParticleSettings)
- Service layers - they're thin wrappers and should test end-to-end

## Fixtures and Factories

**Test Data:**
- Inline instantiation for simple cases:
  ```python
  config = ParticleSettings()  # Loads from env vars set by setup_env fixture
  exc = ParticleAPIError("Server error", 500, {"error": "details"})
  ```

- Dictionary-based data for complex structures:
  ```python
  event_dict = {
      "first_name": "John",
      "last_name": "Doe",
      "ssn": "123-45-6789",
      "event": "test",
  }
  ```

- Timestamp generation for time-based tests:
  ```python
  from datetime import datetime, timedelta, timezone
  expiry = datetime.now(tz=timezone.utc) + timedelta(hours=1)
  tm.update("test-token", expires_at=expiry)
  ```

**Location:**
- Fixtures defined at module top level in test file
- No `conftest.py` (could be added if tests grow)
- `setup_env` fixture in `test_core_integration.py`

**Naming convention:**
- Fixtures use descriptive names: `setup_env` (sets environment)
- Fixture decorator: `@pytest.fixture(autouse=True)`

## Coverage

**Requirements:** Not detected in `pyproject.toml`

**Current state:** No coverage measurement configured

**View Coverage (if added):**
```bash
# Install
pip install pytest-cov

# Generate coverage report
pytest --cov=particle --cov-report=html

# View
open htmlcov/index.html
```

## Test Types

**Unit Tests:**
- Scope: Single class or function behavior
- Approach: Instantiate and verify outputs/attributes
- Example: `TestConfig` verifies ParticleSettings loads env vars correctly
- Example: `TestExceptions` verifies exception attributes and hierarchy
- No external dependencies; all local state

**Integration Tests:**
- Scope: Multiple components working together
- Approach: Verify end-to-end workflows
- Example: `TestAuth` tests TokenManager + ParticleAuth interaction
- Example: `TestHTTPClient` verifies context manager lifecycle
- File named `test_core_integration.py` indicates integration focus

**E2E Tests:**
- Framework: Not detected
- Current status: Not present in codebase
- Future approach: Would test complete workflows (patient registration → query → retrieve) against sandbox API

## Common Patterns

**Async Testing:**
- pytest-asyncio 0.24.0 available in dev dependencies
- Not used in current tests (all sync code)
- Pattern when needed:
  ```python
  @pytest.mark.asyncio
  async def test_async_function():
      result = await async_function()
      assert result == expected
  ```

**Error Testing:**
```python
def test_api_error_has_status_code(self):
    """Verify ParticleAPIError includes status code."""
    exc = ParticleAPIError("Server error", 500, {"error": "details"})
    assert exc.status_code == 500
    assert exc.response_body == {"error": "details"}
    assert exc.code == "api_error"
```

**Nested Structure Testing:**
```python
def test_redact_nested_dicts(self):
    """Verify PHI redaction works on nested structures."""
    event_dict = {
        "patient": {
            "first_name": "Jane",
            "email": "jane@example.com",
        }
    }
    result = redact_phi(None, "info", event_dict)
    assert result["patient"]["first_name"] == "[REDACTED]"
    assert result["patient"]["email"] == "[REDACTED]"
```

**List Iteration Testing:**
```python
def test_all_exceptions_inherit_from_base(self):
    """Verify all exceptions inherit from ParticleError."""
    exceptions = [
        ParticleAuthError(),
        ParticleAPIError("test", 500),
        ParticleValidationError("test"),
        # ... more
    ]
    for exc in exceptions:
        assert isinstance(exc, ParticleError)
```

## Test Coverage Analysis

**Well-Tested Areas:**
- `particle/core/exceptions.py`: All exception types and attributes verified
- `particle/core/config.py`: ParticleSettings loading and defaults tested
- `particle/core/logging.py`: PHI redaction (key-based and pattern-based) thoroughly tested
- `particle/core/auth.py`: TokenManager state and token expiry logic tested
- Core module exports: `__all__` list and accessibility verified

**Gaps/Not Tested:**
- `particle/core/http.py`: ParticleHTTPClient creation and context manager verified, but no HTTP request/response handling tests (would need mocking)
- `particle/patient/`: No tests for PatientService or PatientRegistration validation
- `particle/query/`: No tests for QueryService methods or polling logic
- `particle/document/`: No tests for DocumentService or document submission
- Workflows: No tests for `workflows/*.py` scripts
- Quick-starts: No tests for `quick-starts/python/*.py` examples
- Validation: No tests for Pydantic validators (SSN, telephone, postal code formats)
- Integration: No end-to-end tests against actual API (even in sandbox)
- Error scenarios: Limited testing of actual HTTP error handling

---

*Testing analysis: 2026-02-07*
