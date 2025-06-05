#!/bin/bash

# E2E Test Runner Script
# Usage: ./scripts/run-e2e-tests.sh [test-suite] [browser]

set -e

# Configuration
TEST_SUITE=${1:-"all"}
BROWSER=${2:-"chrome"}
HEADLESS=${E2E_HEADLESS:-"true"}
CLEANUP=${E2E_CLEANUP:-"true"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Stylize MCP E2E Test Runner${NC}"
echo -e "${BLUE}================================${NC}"
echo -e "Test Suite: ${YELLOW}$TEST_SUITE${NC}"
echo -e "Browser: ${YELLOW}$BROWSER${NC}"
echo -e "Headless: ${YELLOW}$HEADLESS${NC}"
echo ""

# Check dependencies
echo -e "${BLUE}📋 Checking dependencies...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is required but not installed${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is required but not installed${NC}"
    exit 1
fi

if ! command -v pytest &> /dev/null; then
    echo -e "${YELLOW}⚠️  pytest not found, installing E2E dependencies...${NC}"
    pip install -r requirements-e2e.txt
fi

echo -e "${GREEN}✅ Dependencies OK${NC}"
echo ""

# Create fake credentials if needed
if [ ! -f "fake-credentials.json" ]; then
    echo -e "${BLUE}🔑 Creating fake credentials...${NC}"
    echo '{}' > fake-credentials.json
fi

# Start services
echo -e "${BLUE}🚀 Starting test services...${NC}"

# Clean up any existing containers
if [ "$CLEANUP" = "true" ]; then
    docker-compose -f docker-compose.e2e.yml down -v >/dev/null 2>&1 || true
fi

# Start infrastructure services
echo "  Starting infrastructure services..."
docker-compose -f docker-compose.e2e.yml up -d firestore-emulator gcs-emulator redis

# Start Selenium based on browser choice
if [ "$BROWSER" = "firefox" ]; then
    echo "  Starting Firefox Selenium..."
    docker-compose -f docker-compose.e2e.yml up -d selenium-firefox
    SELENIUM_URL="http://localhost:4445/wd/hub"
else
    echo "  Starting Chrome Selenium..."
    docker-compose -f docker-compose.e2e.yml up -d selenium-chrome
    SELENIUM_URL="http://localhost:4444/wd/hub"
fi

# Wait for services to be ready
echo -e "${BLUE}⏳ Waiting for services to be ready...${NC}"

wait_for_service() {
    local url=$1
    local name=$2
    local timeout=60
    
    echo -n "  Waiting for $name..."
    while [ $timeout -gt 0 ]; do
        if curl -f $url >/dev/null 2>&1; then
            echo -e " ${GREEN}✅${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
        timeout=$((timeout - 2))
    done
    echo -e " ${RED}❌ Timeout${NC}"
    return 1
}

wait_for_service "http://localhost:8081" "Firestore emulator"
wait_for_service "http://localhost:4443/storage/v1/b" "GCS emulator"
wait_for_service "$SELENIUM_URL/status" "Selenium"

# Start application
echo "  Starting application..."
docker-compose -f docker-compose.e2e.yml up -d app

wait_for_service "http://localhost:8080/health" "Application"

echo -e "${GREEN}✅ All services ready${NC}"
echo ""

# Determine test files to run
determine_test_files() {
    case $TEST_SUITE in
        "all")
            echo "tests/e2e/"
            ;;
        "trial"|"trial_journey")
            echo "tests/e2e/test_trial_user_journey.py"
            ;;
        "mcp"|"mcp_integration")
            echo "tests/e2e/test_mcp_ai_integration.py"
            ;;
        "credit"|"credit_system")
            echo "tests/e2e/test_credit_system.py"
            ;;
        "cross"|"cross_interface")
            echo "tests/e2e/test_cross_interface_integration.py"
            ;;
        "security")
            echo "tests/e2e/test_security_features.py"
            ;;
        "performance")
            echo "tests/e2e/test_performance.py"
            ;;
        "error"|"errors")
            echo "tests/e2e/test_error_scenarios.py"
            ;;
        *)
            echo "tests/e2e/test_${TEST_SUITE}.py"
            ;;
    esac
}

TEST_FILES=$(determine_test_files)

# Set environment variables
export E2E_ENVIRONMENT=e2e_local
export E2E_BASE_URL=http://localhost:8080
export E2E_BROWSER=$BROWSER
export E2E_HEADLESS=$HEADLESS
export E2E_SELENIUM_GRID=true
export E2E_SELENIUM_HUB_URL=$SELENIUM_URL
export E2E_TEST_API_KEY=e2e-test-key-12345

# Create reports directory
mkdir -p tests/e2e/reports

# Run tests
echo -e "${BLUE}🧪 Running E2E tests...${NC}"
echo -e "Test files: ${YELLOW}$TEST_FILES${NC}"
echo ""

# Build pytest command
PYTEST_CMD="pytest $TEST_FILES -v --tb=short"

# Add markers based on test suite
if [ "$TEST_SUITE" != "all" ] && [ "$TEST_SUITE" != "performance" ]; then
    PYTEST_CMD="$PYTEST_CMD -m 'not slow'"
fi

# Add HTML report
PYTEST_CMD="$PYTEST_CMD --html=tests/e2e/reports/report-${TEST_SUITE}-${BROWSER}.html --self-contained-html"

# Add JSON report
PYTEST_CMD="$PYTEST_CMD --json-report --json-report-file=tests/e2e/reports/report-${TEST_SUITE}-${BROWSER}.json"

# Run the tests
if eval $PYTEST_CMD; then
    echo ""
    echo -e "${GREEN}✅ Tests completed successfully!${NC}"
    EXIT_CODE=0
else
    echo ""
    echo -e "${RED}❌ Tests failed!${NC}"
    EXIT_CODE=1
fi

# Show test results location
echo ""
echo -e "${BLUE}📊 Test reports available at:${NC}"
echo -e "  HTML: ${YELLOW}tests/e2e/reports/report-${TEST_SUITE}-${BROWSER}.html${NC}"
echo -e "  JSON: ${YELLOW}tests/e2e/reports/report-${TEST_SUITE}-${BROWSER}.json${NC}"

# Show logs on failure
if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo -e "${BLUE}🔍 Service logs (last 50 lines):${NC}"
    echo -e "${YELLOW}Application logs:${NC}"
    docker-compose -f docker-compose.e2e.yml logs --tail=50 app
fi

# Cleanup
if [ "$CLEANUP" = "true" ]; then
    echo ""
    echo -e "${BLUE}🧹 Cleaning up...${NC}"
    docker-compose -f docker-compose.e2e.yml down -v
    echo -e "${GREEN}✅ Cleanup complete${NC}"
fi

echo ""
echo -e "${BLUE}🏁 E2E test run finished${NC}"

exit $EXIT_CODE