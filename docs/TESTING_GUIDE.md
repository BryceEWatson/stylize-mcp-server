# Stylize MCP Server - Complete Testing Guide

This guide provides step-by-step instructions to thoroughly test all functionality of the Stylize MCP Server application.

## Prerequisites

- `curl` command-line tool
- `jq` for JSON formatting (optional but recommended)
- A test image file (JPEG or PNG, < 5MB)
- Base64 encoding capability (built into most systems)

## Testing Environment

- **Production URL**: https://stylize-mcp-server-997481449751.us-central1.run.app
- **Project**: stylize-mcp-server (GCP Project ID: 997481449751)
- **Region**: us-central1
- **Status**: ✅ **FULLY OPERATIONAL** - All endpoints tested and working

## Test Suite Overview

1. [Basic Health Checks](#1-basic-health-checks)
2. [API Endpoint Testing](#2-api-endpoint-testing)
3. [MCP Protocol Testing](#3-mcp-protocol-testing)
4. [Image Generation Testing](#4-image-generation-testing)
5. [Error Handling Testing](#5-error-handling-testing)
6. [Performance Testing](#6-performance-testing)
7. [Security Testing](#7-security-testing)

---

## 1. Basic Health Checks

### 1.1 Application Health Status
```bash
curl -s https://stylize-mcp-server-997481449751.us-central1.run.app/health | jq '.'
```

**Expected Response:**
```json
{
  "status": "ok",
  "services": {
    "app": "ok",
    "mcp": "ok",
    "styles": "ok (5 styles)"
  },
  "environment": {
    "GCP_PROJECT_ID": "ok",
    "OPENAI_API_KEY_SECRET_PATH": "ok",
    "REDIS": "not_configured"
  },
  "version": "0.1.0"
}
```

**✅ Pass Criteria:**
- Status is "ok"
- All services show "ok" 
- Environment variables are present
- Version is displayed

### 1.2 Response Time Check
```bash
time curl -s https://stylize-mcp-server-997481449751.us-central1.run.app/health > /dev/null
```

**✅ Pass Criteria:**
- Response time < 2 seconds for cold start
- Response time < 500ms for warm instances

---

## 2. API Endpoint Testing

### 2.1 Styles Catalog Endpoint
```bash
curl -s https://stylize-mcp-server-997481449751.us-central1.run.app/styles | jq '.'
```

**Expected Response:** Array of 5 style objects
```json
[
  {
    "id": "van_gogh",
    "name": "Van Gogh",
    "description": "Transforms images into a style reminiscent of Vincent van Gogh's post-impressionist paintings...",
    "prompt_fragment": "in the style of Vincent van Gogh, with bold, swirling brush strokes and vibrant colors"
  },
  ...
]
```

**✅ Pass Criteria:**
- Returns array of exactly 5 styles
- Each style has: id, name, description, prompt_fragment
- Style IDs: van_gogh, pixel_art, flat_ui_icon, neumorphic_button, abstract_geometric

### 2.2 API Documentation Access
```bash
curl -s https://stylize-mcp-server-997481449751.us-central1.run.app/docs
```

**✅ Pass Criteria:**
- Returns HTML page (status 200)
- Contains "Stylize MCP Server" in title
- Shows API endpoints documentation

---

## 3. MCP Protocol Testing

### 3.1 MCP Endpoint Availability
```bash
curl -s -X POST https://stylize-mcp-server-997481449751.us-central1.run.app/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "initialize", "id": 1, "params": {"capabilities": {}}}' | jq '.'
```

**✅ Pass Criteria:**
- Returns valid JSON-RPC response
- No 404 or 500 errors
- Response contains MCP protocol information

### 3.2 MCP Tools Discovery
```bash
curl -s -X POST https://stylize-mcp-server-997481449751.us-central1.run.app/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "id": 2, "params": {}}' | jq '.'
```

**Expected Tools:**
- `stylize_image`
- `list_styles` 
- `get_style_details`
- `generate_image_from_text`

**✅ Pass Criteria:**
- Returns array of tool definitions
- Each tool has name, description, and input schema
- All 4 expected tools are present

### 3.3 MCP Resources Discovery
```bash
curl -s -X POST https://stylize-mcp-server-997481449751.us-central1.run.app/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "resources/list", "id": 3, "params": {}}' | jq '.'
```

**Expected Resources:**
- `styles://catalog`

**✅ Pass Criteria:**
- Returns array with styles catalog resource
- Resource has proper URI and description

---

## 4. Image Generation Testing

### 4.1 Prepare Test Image
```bash
# Create a simple test image or use an existing one
# Convert to base64
cat your_test_image.jpg | base64 -w 0 > test_image_base64.txt
```

### 4.2 Text-Only Generation Test
```bash
curl -s -X POST https://stylize-mcp-server-997481449751.us-central1.run.app/stylize_image \
  -F "style_id=van_gogh" \
  -F "user_prompt=a beautiful sunset over mountains" | jq '.'
```

**Expected Response:**
```json
{
  "original_id": "uuid-string",
  "style": "van_gogh",
  "stylized_image_url": "https://storage.googleapis.com/..."
}
```

**✅ Pass Criteria:**
- Returns JSON with original_id, style, and stylized_image_url
- URL is accessible and returns an image
- Generation completes within 30 seconds

### 4.3 Image Upload and Stylization Test
```bash
curl -s -X POST https://stylize-mcp-server-997481449751.us-central1.run.app/stylize_image \
  -F "image=@your_test_image.jpg" \
  -F "style_id=pixel_art" \
  -F "user_prompt=make it retro gaming style" | jq '.'
```

**✅ Pass Criteria:**
- Accepts image upload successfully
- Returns stylized image URL
- Original and stylized images are different
- Processing completes within 45 seconds

### 4.4 Project Context Test
```bash
curl -s -X POST https://stylize-mcp-server-997481449751.us-central1.run.app/stylize_image \
  -F "style_id=flat_ui_icon" \
  -F "user_prompt=app icon for a music player" \
  -F 'project_context_str={"brand_name":"MusicApp","brand_colors":["#3498db","#e74c3c"],"target_audience":"young adults","mood":"energetic"}' | jq '.'
```

**✅ Pass Criteria:**
- Accepts project context JSON
- Incorporates context into generation
- Returns valid stylized image URL

### 4.5 Download Generated Images
```bash
# Test that generated URLs are accessible
wget -O generated_image.png "STYLIZED_IMAGE_URL_FROM_PREVIOUS_TEST"
file generated_image.png
```

**✅ Pass Criteria:**
- Image downloads successfully
- File is valid PNG/JPEG format
- Image size > 0 bytes
- Image displays correctly

---

## 5. Error Handling Testing

### 5.1 Invalid Style ID Test
```bash
curl -s -X POST https://stylize-mcp-server-997481449751.us-central1.run.app/stylize_image \
  -F "style_id=invalid_style" \
  -F "user_prompt=test prompt"
```

**Expected Response:** HTTP 400 with error message listing valid styles

### 5.2 Missing Required Fields Test
```bash
curl -s -X POST https://stylize-mcp-server-997481449751.us-central1.run.app/stylize_image
```

**Expected Response:** HTTP 400 with error about missing style_id

### 5.3 Invalid Image Format Test
```bash
echo "not an image" > fake_image.txt
curl -s -X POST https://stylize-mcp-server-997481449751.us-central1.run.app/stylize_image \
  -F "image=@fake_image.txt" \
  -F "style_id=van_gogh"
```

**Expected Response:** HTTP 400 with error about invalid image format

### 5.4 Large File Upload Test
```bash
# Create a file larger than 5MB
dd if=/dev/zero of=large_file.jpg bs=1M count=6
curl -s -X POST https://stylize-mcp-server-997481449751.us-central1.run.app/stylize_image \
  -F "image=@large_file.jpg" \
  -F "style_id=van_gogh"
```

**Expected Response:** HTTP 400 with error about file size limit

### 5.5 Invalid Project Context JSON Test
```bash
curl -s -X POST https://stylize-mcp-server-997481449751.us-central1.run.app/stylize_image \
  -F "style_id=van_gogh" \
  -F "user_prompt=test" \
  -F 'project_context_str=invalid json'
```

**Expected Response:** HTTP 400 with JSON parsing error

**✅ Pass Criteria for Error Tests:**
- All return appropriate HTTP status codes (400, 404, 500)
- Error messages are descriptive and helpful
- No server crashes or unhandled exceptions

---

## 6. Performance Testing

### 6.1 Cold Start Test
```bash
# Wait 10 minutes for instance to scale down, then test
sleep 600
time curl -s https://stylize-mcp-server-997481449751.us-central1.run.app/health
```

**✅ Pass Criteria:**
- Cold start completes within 10 seconds
- No timeout errors

### 6.2 Concurrent Request Test
```bash
# Test multiple simultaneous requests
for i in {1..5}; do
  curl -s https://stylize-mcp-server-997481449751.us-central1.run.app/styles > /dev/null &
done
wait
```

**✅ Pass Criteria:**
- All requests complete successfully
- No rate limiting or errors
- Response times remain reasonable

### 6.3 Image Generation Load Test
```bash
# Test multiple image generations (use small prompts to reduce costs)
for i in {1..3}; do
  curl -s -X POST https://stylize-mcp-server-997481449751.us-central1.run.app/stylize_image \
    -F "style_id=van_gogh" \
    -F "user_prompt=simple test $i" &
done
wait
```

**✅ Pass Criteria:**
- All generations complete successfully
- No OpenAI rate limiting errors
- Reasonable processing times

---

## 7. Security Testing

### 7.1 CORS Headers Test
```bash
curl -s -H "Origin: https://example.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -X OPTIONS https://stylize-mcp-server-997481449751.us-central1.run.app/health -v
```

**✅ Pass Criteria:**
- Returns appropriate CORS headers
- Allows cross-origin requests

### 7.2 Input Sanitization Test
```bash
curl -s -X POST https://stylize-mcp-server-997481449751.us-central1.run.app/stylize_image \
  -F "style_id=van_gogh" \
  -F "user_prompt=<script>alert('xss')</script>"
```

**✅ Pass Criteria:**
- Handles potentially malicious input safely
- No XSS vulnerabilities
- No server errors

### 7.3 SQL Injection Simulation
```bash
curl -s -X POST https://stylize-mcp-server-997481449751.us-central1.run.app/stylize_image \
  -F "style_id=van_gogh'; DROP TABLE users; --" \
  -F "user_prompt=test"
```

**✅ Pass Criteria:**
- Returns validation error for invalid style_id
- No database errors or crashes

---

## 8. MCP Tool Testing via JSON-RPC

### 8.1 Test MCP Stylize Image Tool
```bash
# Convert test image to base64 first
IMAGE_BASE64=$(cat your_test_image.jpg | base64 -w 0)

curl -s -X POST https://stylize-mcp-server-997481449751.us-central1.run.app/mcp \
  -H "Content-Type: application/json" \
  -d "{
    \"jsonrpc\": \"2.0\",
    \"method\": \"tools/call\",
    \"id\": 4,
    \"params\": {
      \"name\": \"stylize_image\",
      \"arguments\": {
        \"image_base64\": \"$IMAGE_BASE64\",
        \"style_id\": \"van_gogh\",
        \"user_prompt\": \"make it artistic\"
      }
    }
  }" | jq '.'
```

### 8.2 Test MCP List Styles Tool
```bash
curl -s -X POST https://stylize-mcp-server-997481449751.us-central1.run.app/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "id": 5,
    "params": {
      "name": "list_styles",
      "arguments": {}
    }
  }' | jq '.'
```

### 8.3 Test MCP Generate from Text Tool
```bash
curl -s -X POST https://stylize-mcp-server-997481449751.us-central1.run.app/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "id": 6,
    "params": {
      "name": "generate_image_from_text",
      "arguments": {
        "prompt": "a futuristic city at sunset",
        "style_id": "pixel_art"
      }
    }
  }' | jq '.'
```

**✅ Pass Criteria for MCP Tools:**
- All tools execute successfully via JSON-RPC
- Return properly formatted JSON-RPC responses
- Tool outputs match REST API functionality

---

## 9. Integration Testing Checklist

### Complete End-to-End Test
Run this comprehensive test that exercises the full pipeline:

```bash
#!/bin/bash
echo "🚀 Starting Complete Integration Test..."

# 1. Health check
echo "1. Testing health endpoint..."
curl -s https://stylize-mcp-server-997481449751.us-central1.run.app/health | jq '.status'

# 2. Styles catalog
echo "2. Testing styles endpoint..."
STYLE_COUNT=$(curl -s https://stylize-mcp-server-997481449751.us-central1.run.app/styles | jq 'length')
echo "   Found $STYLE_COUNT styles"

# 3. MCP initialization
echo "3. Testing MCP initialization..."
curl -s -X POST https://stylize-mcp-server-997481449751.us-central1.run.app/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "initialize", "id": 1, "params": {"capabilities": {}}}' | jq '.result.capabilities'

# 4. Text-only image generation
echo "4. Testing text-only generation..."
RESPONSE=$(curl -s -X POST https://stylize-mcp-server-997481449751.us-central1.run.app/stylize_image \
  -F "style_id=van_gogh" \
  -F "user_prompt=a simple landscape")
IMAGE_URL=$(echo $RESPONSE | jq -r '.stylized_image_url')
echo "   Generated image: $IMAGE_URL"

# 5. Test image download
echo "5. Testing image download..."
curl -s -o test_output.png "$IMAGE_URL"
FILE_SIZE=$(wc -c < test_output.png)
echo "   Downloaded image size: $FILE_SIZE bytes"

echo "✅ Integration test complete!"
```

---

## 10. Monitoring and Logging

### 10.1 Check Application Logs
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=stylize-mcp-server" \
  --limit=20 --format="table(timestamp,severity,textPayload)"
```

### 10.2 Monitor Error Rates
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=stylize-mcp-server AND severity>=ERROR" \
  --limit=10 --format="table(timestamp,severity,textPayload)"
```

---

## Test Results Tracking

Create a simple test results tracker:

```bash
# Create test results file
cat > test_results.txt << EOF
# Stylize MCP Server Test Results - $(date)

## Basic Health Checks
[ ] Health endpoint returns 200 OK
[ ] All services show "ok" status
[ ] Response time < 2 seconds

## API Endpoints
[ ] Styles endpoint returns 5 styles
[ ] API documentation accessible
[ ] CORS headers present

## MCP Protocol
[ ] MCP endpoint responds to JSON-RPC
[ ] 4 tools available via MCP
[ ] Resources endpoint works

## Image Generation
[ ] Text-only generation works
[ ] Image upload and stylization works
[ ] Generated images downloadable
[ ] Project context integration works

## Error Handling
[ ] Invalid style ID returns 400
[ ] Missing fields return 400
[ ] Large files rejected properly
[ ] Invalid JSON handled gracefully

## Performance
[ ] Cold start < 10 seconds
[ ] Concurrent requests handled
[ ] No rate limiting issues

## Security
[ ] Input sanitization working
[ ] No XSS vulnerabilities
[ ] CORS configured correctly

## Overall Status: [ PASS / FAIL ]

Notes:
- 
- 
- 
EOF

echo "Test results template created in test_results.txt"
```

---

## Common Issues and Troubleshooting

### Issue: "Service Unavailable" errors
- **Check**: Cloud Run service status
- **Action**: Restart service or check logs

### Issue: Image generation timeouts
- **Check**: OpenAI API key configuration
- **Action**: Verify OPENAI_API_KEY_SECRET_PATH environment variable

### Issue: Signed URL failures
- **Check**: GCS service account permissions
- **Action**: Review IAM roles for stylize-mcp-sa

### Issue: MCP tools not responding
- **Check**: FastMCP integration logs
- **Action**: Verify MCP mounting and tool registration

---

## Success Criteria Summary

The application passes all tests if:

✅ **All HTTP endpoints return 2xx status codes**  
✅ **MCP protocol responds properly to JSON-RPC calls**  
✅ **Image generation produces valid downloadable images**  
✅ **Error cases return appropriate error codes and messages**  
✅ **Performance metrics meet acceptable thresholds**  
✅ **Security tests show no vulnerabilities**  

---

*This testing guide ensures comprehensive validation of the Stylize MCP Server application across all functional areas.*