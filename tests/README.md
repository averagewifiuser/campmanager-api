# CampManager API Tests

This directory contains comprehensive tests for the CampManager API application using pytest.

## Test Structure

```
tests/
├── __init__.py              # Test package initialization
├── conftest.py              # Shared fixtures and configuration
├── test_app.py              # Application factory and basic functionality tests
├── test_auth.py             # Authentication and authorization tests
├── test_models.py           # Database model tests
└── README.md                # This file
```

## Test Categories

Tests are organized using pytest markers:

- `@pytest.mark.unit` - Unit tests for individual components
- `@pytest.mark.integration` - Integration tests for component interactions
- `@pytest.mark.auth` - Authentication and authorization tests
- `@pytest.mark.camp` - Camp management functionality tests
- `@pytest.mark.user` - User management tests
- `@pytest.mark.registration` - Registration functionality tests
- `@pytest.mark.slow` - Tests that take longer to run

## Running Tests

### Prerequisites

Install test dependencies:
```bash
pip install -r requirements.txt
```

### Basic Usage

Run all tests:
```bash
pytest
```

Run with verbose output:
```bash
pytest -v
```

Run with coverage report:
```bash
pytest --cov=app --cov-report=term-missing --cov-report=html
```

### Using the Test Runner Script

The project includes a convenient test runner script:

```bash
# Run all tests
python run_tests.py

# Run with coverage
python run_tests.py --coverage

# Run specific test types
python run_tests.py --type unit
python run_tests.py --type integration
python run_tests.py --type auth

# Run specific test file
python run_tests.py --file test_auth.py

# Run specific test function
python run_tests.py --function test_login_valid_credentials

# Run tests with verbose output
python run_tests.py --verbose

# Skip slow tests
python run_tests.py --fast
```

### Test Type Examples

Run only unit tests:
```bash
pytest -m unit
```

Run only authentication tests:
```bash
pytest -m auth
```

Run integration tests excluding slow ones:
```bash
pytest -m "integration and not slow"
```

## Test Configuration

### pytest.ini

The `pytest.ini` file contains project-specific pytest configuration:

- Test discovery patterns
- Coverage settings
- Marker definitions
- Warning filters

### conftest.py

Contains shared fixtures used across all tests:

- **Application fixtures**: `app`, `client`, `app_context`
- **Database fixtures**: `db_session`
- **Sample data fixtures**: `sample_user`, `sample_camp`, etc.
- **Authentication fixtures**: `auth_headers`, `volunteer_auth_headers`
- **Helper functions**: `create_test_user`, `get_auth_token`

## Test Data

### Fixtures

The test suite uses pytest fixtures to provide consistent test data:

- `sample_user` - A test camp manager user
- `sample_volunteer` - A test volunteer user
- `sample_camp` - A test camp with all required fields
- `sample_church` - A test church associated with a camp
- `sample_category` - A test registration category
- `sample_custom_field` - A test custom field
- `sample_registration_link` - A test registration link
- `sample_registration` - A test registration

### Database Isolation

Each test runs in isolation with:
- Fresh database tables created for each test session
- Transaction rollback after each test
- No test data pollution between tests

## Writing Tests

### Test Structure

Follow this structure for new tests:

```python
import pytest

@pytest.mark.unit  # or integration, auth, etc.
class TestFeatureName:
    """Test feature description"""
    
    def test_specific_functionality(self, fixture_name):
        """Test specific functionality description"""
        # Arrange
        # Act
        # Assert
```

### Best Practices

1. **Use descriptive test names** that explain what is being tested
2. **Follow AAA pattern** (Arrange, Act, Assert)
3. **Use appropriate markers** to categorize tests
4. **Mock external dependencies** in unit tests
5. **Test both success and failure cases**
6. **Use fixtures** for common test data
7. **Keep tests independent** - no test should depend on another

### Example Test

```python
@pytest.mark.auth
class TestUserLogin:
    """Test user login functionality"""
    
    def test_login_valid_credentials(self, client, sample_user, sample_user_data):
        """Test successful login with valid credentials"""
        # Arrange
        login_data = {
            'data': {
                'email': sample_user_data['email'],
                'password': sample_user_data['password']
            }
        }
        
        # Act
        response = client.post('/auth/login', json=login_data)
        
        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert 'access_token' in data['data']
        assert 'user' in data['data']
```

## Coverage Reports

### Terminal Report

Run tests with coverage to see a terminal report:
```bash
pytest --cov=app --cov-report=term-missing
```

### HTML Report

Generate an HTML coverage report:
```bash
pytest --cov=app --cov-report=html
```

View the report by opening `htmlcov/index.html` in your browser.

### Coverage Goals

- **Minimum coverage**: 80% (enforced by pytest configuration)
- **Target coverage**: 90%+ for critical components
- **Focus areas**: Models, services, and API endpoints

## Continuous Integration

### GitHub Actions

Example workflow for running tests in CI:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - name: Install dependencies
      run: pip install -r requirements.txt
    - name: Run tests
      run: python run_tests.py --coverage
```

## Debugging Tests

### Running Single Tests

Run a specific test:
```bash
pytest tests/test_auth.py::TestUserLogin::test_login_valid_credentials -v
```

### Using pdb

Add breakpoints in tests:
```python
def test_something(self):
    import pdb; pdb.set_trace()
    # Your test code here
```

Run with pdb:
```bash
pytest --pdb
```

### Verbose Output

Get detailed output:
```bash
pytest -v -s
```

## Common Issues

### Database Issues

If you encounter database-related test failures:
1. Ensure test database is properly isolated
2. Check that fixtures are properly cleaning up
3. Verify database migrations are up to date

### Import Issues

If tests can't import application modules:
1. Ensure you're running tests from the project root
2. Check that `__init__.py` files are present
3. Verify PYTHONPATH includes the project directory

### Fixture Issues

If fixtures aren't working:
1. Check that fixtures are defined in `conftest.py`
2. Ensure fixture scope is appropriate
3. Verify fixture dependencies are correct

## Contributing

When adding new tests:

1. **Follow naming conventions** (`test_*.py` files, `test_*` functions)
2. **Add appropriate markers** for test categorization
3. **Update this README** if adding new test categories or patterns
4. **Ensure tests pass** before submitting
5. **Maintain or improve coverage** - don't decrease overall coverage

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-flask documentation](https://pytest-flask.readthedocs.io/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [Flask testing documentation](https://flask.palletsprojects.com/en/2.0.x/testing/)
