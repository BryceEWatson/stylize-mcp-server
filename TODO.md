# TODO: Fix Deployed Application Critical Issues

## Analysis Summary
Based on deployment testing and log analysis, the application has **2 critical issues** preventing full functionality:

1. **MCP Server Non-Functional** - Router initialization failing silently  
2. **GCS Signed URL Generation** - Credential type mismatch (images generate successfully but download URLs fail)

**✅ RESOLVED:** OpenAI API Key is properly configured and working

## Issue Priority Matrix

| Priority | Issue | Status | Impact |
|----------|-------|--------|--------|
| **P0** | MCP Router Failure | Silent fail | 🔴 MCP protocol unusable |
| **P0** | GCS Signed URLs | Auth error | 🔴 Images generate but no download URLs |
| **P1** | Redis Configuration | Missing | 🟡 Performance degradation |
| ~~P0~~ | ~~OpenAI API Key~~ | ✅ Working | ~~Core functionality broken~~ |

---

## 🔴 PRIORITY 0: Critical Functionality Fixes

### 1. Fix MCP Server Router Initialization (CRITICAL)

**Problem:** `mcp.add_endpoint_to_router()` failing silently, only fallback `/mcp/health` endpoint exists

**Root Cause Analysis:**
- FastMCP integration failing during router setup
- Exception caught but not properly logged in startup
- No actual MCP protocol endpoints available

**Action Items:**
- [ ] **Enhance MCP error logging** - Add detailed exception logging to `get_mcp_router()`
- [ ] **Check FastMCP version compatibility** - Verify `fastmcp>=0.1.0` works with current setup
- [ ] **Test FastMCP dependencies** - Ensure all FastMCP requirements installed
- [ ] **Debug router creation** - Add verbose logging to `mcp.add_endpoint_to_router()` call
- [ ] **Validate Redis fallback** - Ensure in-memory mode works correctly
- [ ] **Test MCP protocol endpoints** - Verify proper SSE/WebSocket endpoints created

**Expected Outcomes:**
- MCP endpoints accessible at `/mcp` (SSE/WebSocket)
- MCP tools (`stylize_image`, `list_styles`) functional
- Proper MCP protocol communication working

### 2. ✅ OpenAI API Key Status (RESOLVED)

**Problem:** ~~OpenAI service initialized but API key missing from Secret Manager~~

**✅ VERIFIED WORKING:**
- Secret Manager: `OPENAI_API_KEY` secret exists with valid `sk-proj...` key
- Environment: `OPENAI_API_KEY_SECRET_PATH=projects/stylize-mcp-server/secrets/OPENAI_API_KEY/versions/latest`
- Service: OpenAI service initializes successfully
- Functionality: Images are being generated successfully (per logs)

**Root Cause of 500 Errors:** GCS signed URL generation, NOT OpenAI API key

**Evidence from Logs:**
```
2025-05-23 16:23:44,233 - app.gcs_service - INFO - Successfully uploaded image to stylize-variants-stylize-mcp-server/32c30f09-8a3d-4590-9faf-8a28a8008010/van_gogh.png (size: 2128379 bytes, content-type: image/png)
```
Images are generated and uploaded successfully; failure occurs at signed URL step.

---

## 🟡 PRIORITY 1: Infrastructure Fixes

### 2. Fix GCS Signed URL Generation (CRITICAL - NOW P0)

**Problem:** Service account using Compute Engine credentials instead of private key credentials

**Impact:** Images generate successfully but users cannot download them (500 error)

**Error Details:**
```
AttributeError: you need a private key to sign credentials
google.auth.exceptions.RefreshError: Permission 'iam.serviceAccounts.getAccessToken' denied
```

**Current Status:** 
- Images upload to GCS successfully
- OpenAI generation working
- Only signed URL creation failing

**Action Items:**
- [ ] **Review IAM configuration** - Check `infra/iam.tf` for service account setup
- [ ] **Fix service account credentials** - Ensure Cloud Run uses private key credentials
- [ ] **Grant Token Creator role** - Add `iam.serviceAccounts.getAccessToken` permission
- [ ] **Alternative: Use public URLs** - Consider making GCS buckets publicly readable
- [ ] **Test credential types** - Verify proper credential propagation to Cloud Run

**Expected Outcomes:**
- Signed URLs generated successfully
- Download links functional
- Complete image workflow working

---

## 🟡 PRIORITY 2: Performance Optimizations

### 4. Configure Redis (Memorystore)

**Problem:** Redis not configured, using in-memory fallback

**Current Status:**
- Environment shows: `"REDIS": "not_configured"`
- MCP using in-memory cache only

**Action Items:**
- [ ] **Deploy Redis Memorystore** - Use Terraform to create Redis instance
- [ ] **Configure environment variables** - Set `REDIS_HOST` and `REDIS_PORT` in Cloud Run
- [ ] **Test Redis connectivity** - Verify Cloud Run can reach Redis instance
- [ ] **Update VPC configuration** - Ensure proper network access

**Expected Outcomes:**
- MCP tool response caching across instances
- Better performance under load
- Persistent session state

---

## Implementation Plan

### Phase 1: Emergency Fixes (Day 1)
1. ✅ ~~Add OpenAI API key to Secret Manager~~ ⏱️ ~~30 mins~~ (ALREADY WORKING)
2. Fix MCP router logging and debug initialization ⏱️ 2 hours
3. Fix GCS signed URL credentials ⏱️ 2 hours
4. Test basic functionality restoration ⏱️ 30 mins

### Phase 2: Infrastructure Fixes (Day 2)
1. Deploy and configure Redis ⏱️ 2 hours
2. End-to-end testing ⏱️ 1 hour

### Phase 3: Validation & Monitoring (Day 3)
1. Comprehensive integration testing ⏱️ 2 hours
2. Performance testing ⏱️ 1 hour
3. Documentation updates ⏱️ 1 hour

---

## Testing Checklist

### Core Functionality Tests
- [ ] Health endpoint: `GET /health` ✅ Working
- [ ] Styles endpoint: `GET /styles` ✅ Working  
- [ ] MCP health: `GET /mcp/health` ✅ Working (degraded)
- [ ] MCP protocol: Connect to `/mcp` via SSE/WebSocket ❌ Broken
- [ ] Image generation: `POST /stylize_image` ⚠️ Partial (generates but no download URL)
- [ ] Image download: Signed URL access ❌ Broken (credentials)

### Integration Tests
- [ ] Full MCP tool workflow
- [ ] End-to-end image generation with download
- [ ] Multi-instance Redis caching
- [ ] Error handling and recovery

---

## Deployment Information

- **Service**: `stylize-mcp-server` (us-central1)
- **Current Revision**: `stylize-mcp-server-00023-9rn`
- **URL**: https://stylize-mcp-server-997481449751.us-central1.run.app
- **Project**: `stylize-mcp-server` (997481449751)

## Emergency Rollback Plan

If fixes cause service instability:
1. Revert to previous Cloud Run revision
2. Remove problematic environment variables
3. Restore known-good configuration
4. Document failure for post-mortem analysis