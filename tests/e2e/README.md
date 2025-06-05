# End-to-End Testing Suite

This directory contains comprehensive E2E tests for the Stylize MCP Server project, covering all critical user flows across REST API, MCP, and Web UI interfaces.

## Overview

The E2E testing suite validates:
- **Complete user journeys** from trial discovery to account conversion
- **Cross-interface integration** between Web UI, REST API, and MCP
- **Security and abuse prevention** measures
- **Performance benchmarks** and load handling
- **Error scenarios** and edge cases
- **Credit system** functionality and usage tracking

## Test Structure

### Core Test Suites

1. **`test_trial_user_journey.py`** - Anonymous trial user flow
   - Trial session creation and persistence
   - Image generation limits and enforcement
   - Multi-style generation usage counting
   - Trial-to-account conversion workflow

2. **`test_mcp_ai_integration.py`** - MCP AI assistant integration
   - Complete MCP tool workflow testing
   - API key vs trial session authentication
   - Error handling and recovery
   - Performance benchmarks for MCP tools

3. **`test_credit_system.py`** - Credit purchase and usage
   - Credit package display and purchase flows
   - Usage tracking accuracy across interfaces
   - Insufficient credits handling
   - Dashboard credit information consistency

4. **`test_cross_interface_integration.py`** - Cross-interface testing
   - Trial session usage across Web UI and API
   - User account functionality across all interfaces
   - Data consistency validation
   - Session state persistence

5. **`test_error_scenarios.py`** - Error handling and edge cases
   - OpenAI and GCS service failures
   - Malformed request handling
   - Session expiration scenarios
   - Content policy violations

6. **`test_security_features.py`** - Security and abuse prevention
   - Trial abuse prevention measures
   - Rate limiting behavior
   - Content policy enforcement
   - Authentication security

7. **`test_performance.py`** - Performance and load testing
   - Concurrent image generation
   - Large image upload performance
   - Database performance under load
   - Throughput measurements

### Supporting Infrastructure

- **`conftest.py`** - Pytest configuration and shared fixtures
- **`config.py`** - Environment-specific test configuration
- **`pages/`** - Page Object Model for Web UI testing
- **`utils/`** - Utility classes for API and MCP clients
- **`data/`** - Test data and fixtures

## Quick Start

### Prerequisites

1. **Python 3.11+** with pip
2. **Docker and Docker Compose** for service orchestration
3. **Chrome/Firefox** for web UI testing (or use Selenium Grid)

### Installation

```bash
# Install E2E test dependencies
pip install -r requirements-e2e.txt

# Create test environment file (optional)
cp .env.example .env.e2e
```

### Running Tests

#### Local Development Testing

```bash
# Start services and run all tests
docker-compose -f docker-compose.e2e.yml up --build

# Run specific test suite
pytest tests/e2e/test_trial_user_journey.py -v

# Run with specific browser
E2E_BROWSER=firefox pytest tests/e2e/ -v

# Run without slow tests
pytest tests/e2e/ -m "not slow" -v
```

#### Production-Like Testing

```bash
# Test against staging environment
E2E_ENVIRONMENT=staging E2E_BASE_URL=https://staging.example.com pytest tests/e2e/

# Test with real OpenAI API (limited quota)
E2E_OPENAI_API_KEY=your_key pytest tests/e2e/ -m "requires_openai"
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `E2E_ENVIRONMENT` | `local` | Test environment (`local`, `staging`, `production`) |
| `E2E_BASE_URL` | `http://localhost:8080` | Application base URL |
| `E2E_BROWSER` | `chrome` | Browser for web UI tests (`chrome`, `firefox`) |
| `E2E_HEADLESS` | `true` | Run browser in headless mode |
| `E2E_SELENIUM_GRID` | `false` | Use Selenium Grid for browser testing |
| `E2E_TEST_API_KEY` | - | API key for authenticated testing |
| `E2E_OPENAI_API_KEY` | - | OpenAI API key for real integration tests |
| `E2E_TEST_SECURITY` | `true` | Enable security feature testing |
| `E2E_PARALLEL_TESTS` | `true` | Run tests in parallel |
| `E2E_MAX_RETRIES` | `2` | Maximum test retries on failure |

### Docker Compose Services

The `docker-compose.e2e.yml` orchestrates:

- **app** - Main application with test configuration
- **firestore-emulator** - Local Firestore for database operations
- **gcs-emulator** - Local GCS for file storage
- **redis** - Caching layer (optional)
- **selenium-chrome/firefox** - Browser automation
- **e2e-tests** - Test runner container

## Test Categories and Markers

### Pytest Markers

```bash
# Run only integration tests
pytest tests/e2e/ -m "integration"

# Run only web UI tests
pytest tests/e2e/ -m "web_ui"

# Run only API tests
pytest tests/e2e/ -m "api_only"

# Run only MCP tests
pytest tests/e2e/ -m "mcp_only"

# Run security tests
pytest tests/e2e/ -m "security"

# Run performance tests
pytest tests/e2e/ -m "performance"

# Skip slow tests
pytest tests/e2e/ -m "not slow"

# Run tests requiring real OpenAI API
pytest tests/e2e/ -m "requires_openai"
```

### Test Categories

- **`integration`** - End-to-end integration tests
- **`web_ui`** - Tests requiring browser automation
- **`api_only`** - REST API only tests
- **`mcp_only`** - MCP protocol only tests
- **`security`** - Security and abuse prevention tests
- **`performance`** - Performance and load tests
- **`slow`** - Tests that take longer to execute

## CI/CD Integration

### GitHub Actions Workflow

The `.github/workflows/e2e-tests.yml` provides:

- **Automated E2E testing** on pull requests and pushes
- **Daily scheduled runs** for regression detection
- **Manual workflow dispatch** with configurable parameters
- **Cross-browser testing** (Chrome and Firefox)
- **Parallel test execution** for faster results
- **Test report generation** and artifact uploading

### Workflow Triggers

```yaml
# On pull requests to main (when E2E files change)
on:
  pull_request:
    branches: [main]
    paths:
      - 'app/**'
      - 'tests/e2e/**'
      - 'requirements*.txt'
      - 'docker-compose*.yml'
      - 'Dockerfile*'

# Manual trigger with options
on:
  workflow_dispatch:
    inputs:
      test_suite: [all, trial_journey, mcp_integration, ...]
      browser: [chrome, firefox, both]
      environment: [local, staging]

# Via PR label in main CI workflow
# Add "run-e2e" label to any PR to trigger core E2E tests
```

## Test Data Management

### Test Images

The `TestDataManager` generates various test images:

- **Valid images** - JPEG and PNG in different sizes
- **Invalid images** - Corrupted, oversized, wrong format
- **Logo images** - For project context testing

### Project Contexts

Predefined project contexts for testing:

- **Minimal context** - Basic brand colors and mood
- **Complete context** - Full brand guidelines with logo
- **Invalid contexts** - For error testing

### User Data

Randomly generated test user data:

- **Unique email addresses** with timestamps
- **Valid registration information**
- **Test company data**

## Best Practices

### Writing Tests

1. **Use Page Object Model** for web UI interactions
2. **Implement proper cleanup** in fixtures and teardown
3. **Add meaningful assertions** with clear error messages
4. **Use appropriate markers** for test categorization
5. **Handle async operations** properly with asyncio

### Test Organization

1. **Group related tests** in the same test class
2. **Use descriptive test names** that explain the scenario
3. **Document complex test flows** with comments
4. **Separate setup logic** into fixtures
5. **Keep tests independent** and idempotent

### Performance Considerations

1. **Use parallel execution** where possible
2. **Share expensive resources** via session-scoped fixtures
3. **Clean up test data** to avoid interference
4. **Monitor test execution time** and optimize slow tests
5. **Use appropriate timeouts** for async operations

## Debugging and Troubleshooting

### Common Issues

1. **Service startup timeouts**
   ```bash
   # Check service logs
   docker-compose -f docker-compose.e2e.yml logs app
   
   # Verify service health
   curl http://localhost:8080/health
   ```

2. **Selenium connection failures**
   ```bash
   # Check Selenium status
   curl http://localhost:4444/wd/hub/status
   
   # Use VNC to debug (password: secret)
   vncviewer localhost:5900
   ```

3. **Test data conflicts**
   ```bash
   # Clean up test data
   docker-compose -f docker-compose.e2e.yml down -v
   ```

### Debug Mode

```bash
# Run with debug output
pytest tests/e2e/ -v -s --tb=long

# Run single test with debugging
pytest tests/e2e/test_trial_user_journey.py::TestTrialUserJourney::test_complete_trial_to_conversion_flow -v -s

# Enable browser debugging (non-headless)
E2E_HEADLESS=false pytest tests/e2e/ -v
```

### Log Analysis

```bash
# View application logs
docker-compose -f docker-compose.e2e.yml logs -f app

# View test execution logs
pytest tests/e2e/ --log-cli-level=DEBUG

# Generate HTML report with logs
pytest tests/e2e/ --html=reports/report.html --self-contained-html
```

## Monitoring and Reporting

### Test Reports

Tests generate comprehensive reports:

- **HTML reports** with test results and screenshots
- **JSON reports** for programmatic analysis
- **Performance metrics** and benchmarks
- **Security test results** and compliance checks

### Metrics Tracking

Key metrics monitored:

- **Test execution time** and performance trends
- **Success/failure rates** across test suites
- **Cross-browser compatibility** results
- **Security test coverage** and compliance
- **Performance benchmark** trends over time

### Alerting

Automated alerts for:

- **Failed test runs** in CI/CD
- **Performance regression** detection
- **Security test failures**
- **Service availability** issues

## Contributing

### Adding New Tests

1. **Identify the test category** and appropriate test file
2. **Follow existing patterns** for test structure
3. **Add appropriate markers** and documentation
4. **Include error handling** and cleanup
5. **Update this README** if adding new test categories

### Test Review Guidelines

1. **Verify test independence** and repeatability
2. **Check performance impact** of new tests
3. **Ensure proper error handling** and cleanup
4. **Validate cross-browser compatibility**
5. **Review security implications** of test data

### Maintenance

1. **Update test data** as application evolves
2. **Maintain browser driver versions**
3. **Monitor test execution performance**
4. **Update documentation** for new features
5. **Review and update timeouts** as needed

## Related Documentation

- [Testing Guide](../../docs/TESTING_GUIDE.md) - Comprehensive testing documentation
- [Security Configuration](../../docs/SECURITY_CONFIGURATION.md) - Security testing setup
- [API Reference](../../docs/developer-guide/api-reference.md) - API endpoint documentation
- [MCP Integration](../../docs/developer-guide/mcp-integration.md) - MCP testing guide