#!/bin/bash
# Simple curl-based test script for Stylize MCP Server
# No Python dependencies required

BASE_URL="${1:-https://stylize-mcp-server-997481449751.us-central1.run.app}"

echo "🧪 Testing Stylize MCP Server"
echo "📍 Base URL: $BASE_URL"
echo "================================================"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Function to test endpoint
test_endpoint() {
    local test_name="$1"
    local method="$2"
    local endpoint="$3"
    local expected_status="$4"
    local data="$5"
    
    echo -e "\n🔍 Testing: $test_name"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$BASE_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$BASE_URL$endpoint" $data)
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "$expected_status" ]; then
        echo -e "${GREEN}✅ PASS${NC} - HTTP $http_code"
        echo "Response: $(echo $body | jq -c . 2>/dev/null || echo $body | head -c 100)..."
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC} - Expected HTTP $expected_status, got $http_code"
        echo "Response: $body"
        ((FAILED++))
    fi
}

# Test 1: Health check
test_endpoint "Health Check" "GET" "/health" "200"

# Test 2: Get styles
test_endpoint "Get Available Styles" "GET" "/styles" "200"

# Test 3: Test with missing required fields (should fail)
# Note: Deployed version returns 400, new code returns 422
test_endpoint "Missing Required Fields" "POST" "/stylize_image" "400" \
    "-F 'user_prompt=test'"

# Test 4: Test with invalid style_id (should fail)
# Create a small test image
echo "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=" | base64 -d > /tmp/test_image.png

test_endpoint "Invalid Style ID" "POST" "/stylize_image" "400" \
    "-F 'image=@/tmp/test_image.png' -F 'style_id=invalid_style_xyz'"

# Test 5: Basic stylization (this will actually call OpenAI API)
echo -e "\n⚠️  Skipping actual image generation test (would incur OpenAI costs)"
echo "To test actual generation, run:"
echo "curl -X POST '$BASE_URL/stylize_image' \\"
echo "  -F 'image=@your_image.png' \\"
echo "  -F 'style_id=van_gogh' \\"
echo "  -F 'user_prompt=A peaceful landscape'"

# Clean up
rm -f /tmp/test_image.png

# Summary
echo -e "\n================================================"
echo "📊 Test Summary"
echo "================================================"
echo -e "Total tests: $((PASSED + FAILED))"
echo -e "${GREEN}✅ Passed: $PASSED${NC}"
echo -e "${RED}❌ Failed: $FAILED${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 All tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}⚠️  Some tests failed${NC}"
    exit 1
fi