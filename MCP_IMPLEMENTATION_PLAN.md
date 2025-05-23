# MCP Implementation Plan for Stylize Server

## Overview
This plan details the steps needed to properly implement MCP (Model Context Protocol) support in the Stylize MCP Server.

## Current Issues
1. MCP endpoint returns "unavailable" in health check
2. The `stylize_image_mcp_tool` is just a placeholder
3. FastMCP is in requirements.txt but may not be properly initialized

## Implementation Steps

### Phase 1: Fix MCP Service Integration (Immediate)

1. **Update MCP Tool Implementation**
   - Replace placeholder `stylize_image_mcp_tool` with actual implementation
   - Integrate with existing OpenAI and GCS services
   - Add proper error handling

2. **Fix MCP Router Registration**
   - Ensure MCP router is properly included in FastAPI app
   - Add proper health check for MCP service
   - Handle initialization errors gracefully

### Phase 2: Enhance MCP Capabilities

1. **Add Multiple MCP Tools**
   ```python
   @mcp.tool()
   async def stylize_image(image_base64: str, style_id: str, user_prompt: Optional[str] = None) -> Dict[str, str]:
       """Stylize an image with the specified style."""
   
   @mcp.tool()
   async def list_styles() -> List[Dict[str, str]]:
       """List all available styles."""
   
   @mcp.tool()
   async def get_style_details(style_id: str) -> Dict[str, str]:
       """Get details about a specific style."""
   ```

2. **Add MCP Resources**
   ```python
   @mcp.resource("styles://catalog")
   async def styles_catalog() -> str:
       """Provide the complete styles catalog as a resource."""
   ```

### Phase 3: Testing Strategy

1. **Local Testing**
   - Test with Claude Desktop or other MCP clients
   - Verify Server-Sent Events (SSE) stream
   - Test all MCP tools with various inputs

2. **Integration Testing**
   - Test MCP endpoint alongside REST API
   - Ensure proper error handling
   - Verify authentication/authorization if needed

3. **Production Testing**
   - Deploy to Cloud Run
   - Test with production MCP clients
   - Monitor logs and performance

### Phase 4: Documentation

1. **MCP Client Configuration**
   ```json
   {
     "mcpServers": {
       "stylize": {
         "url": "https://stylize-mcp-server-997481449751.us-central1.run.app/mcp",
         "description": "AI-powered image stylization service"
       }
     }
   }
   ```

2. **Usage Examples**
   - How to connect from Claude Desktop
   - Example tool invocations
   - Error handling guidance

## Technical Requirements

### Dependencies
- fastmcp>=0.1.0 (already in requirements.txt)
- All existing dependencies for image processing

### Environment Variables
- No additional env vars needed for basic MCP
- Optional: MCP_AUTH_TOKEN for authentication

### Infrastructure
- Cloud Run must support WebSocket/SSE connections
- No additional infrastructure needed

## Implementation Timeline

1. **Day 1**: Fix current implementation
   - Update mcp_server.py with real implementation
   - Test locally
   - Deploy fixes

2. **Day 2**: Enhance and test
   - Add additional MCP tools
   - Comprehensive testing
   - Documentation

3. **Day 3**: Production ready
   - Final testing
   - Documentation updates
   - Announce availability

## Success Criteria

1. MCP health check shows "available"
2. All MCP tools work correctly
3. Can connect from MCP clients (Claude Desktop, etc.)
4. Proper error handling and logging
5. Documentation is complete

## Code Changes Needed

### 1. Update app/mcp_server.py
- Implement real stylize_image tool
- Add dependency injection for services
- Add proper error handling

### 2. Update app/main.py
- Ensure MCP router is properly initialized
- Add MCP-specific health check

### 3. Add tests/test_mcp.py
- Unit tests for MCP tools
- Integration tests for MCP endpoint

### 4. Update documentation
- Add MCP section to README.md
- Create MCP_USAGE.md guide