# Stylize MCP Server

## Overview

The Stylize MCP Server is a **fully operational** cloud-based service that transforms user-supplied images into multiple style-specific variants and provides AI agents with image generation capabilities via the Model Context Protocol (MCP). It leverages DALL·E 3 with a curated style bank, template-driven prompt engineering, content-safety filtering, and intelligent caching to deliver high-quality stylized images efficiently.

## ✅ Current Status: **FULLY FUNCTIONAL**

**🚀 Live Production Deployment:**
- **REST API**: https://stylize-mcp-server-997481449751.us-central1.run.app
- **MCP Endpoint**: https://stylize-mcp-server-997481449751.us-central1.run.app/mcp/sse
- **Health Status**: All services operational
- **Image Generation**: Working with public access URLs
- **MCP Integration**: Ready for Claude Desktop and other MCP clients

## Completed Features

✅ **REST API endpoint for image stylization** (`POST /stylize_image`)  
✅ **MCP Server integration** with 4 tools and 1 resource  
✅ **Curated style catalog** with 5 specialized styles  
✅ **DALL·E 3 integration** for high-quality image generation  
✅ **Content safety filtering** with Cloud Vision SafeSearch  
✅ **Public image access** via Google Cloud Storage  
✅ **Cost guardrails** with usage tracking  
✅ **Infrastructure as code** deployed on Google Cloud Platform  
✅ **Comprehensive testing suite** and documentation

## Local Development Setup

### Prerequisites

- Python 3.10 or newer
- pip (Python package manager)
- Google Cloud SDK (for local GCP service emulation)
- OpenAI API key (for DALL·E 3 integration)

### Environment Setup

```bash
# Clone the repository
git clone [repository_url]
cd stylize-mcp-server

# Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux  
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
# Required: GCP_PROJECT_ID, OPENAI_API_KEY_SECRET_PATH
# Optional: REDIS_HOST, REDIS_PORT for caching
```

### Running the Server Locally

```bash
# Start the FastAPI server
uvicorn app.main:app --reload

# The server will be available at http://localhost:8000
# API documentation is available at http://localhost:8000/docs
```

## Project Structure

- `app/`: Application code
- `infra/`: Terraform infrastructure as code
- `docs/`: Project documentation

## API Endpoints

**REST API (Fully Operational):**
- `POST /stylize_image`: Generate a stylized image from an uploaded image, text prompt, or project context ✅
- `GET /styles`: List available styles ✅
- `GET /health`: Server health check ✅
- `GET /docs`: OpenAPI documentation ✅

**MCP Protocol Endpoints:**
- `/mcp/sse`: Server-Sent Events transport for MCP clients ✅
- `/mcp`: JSON-RPC endpoint for MCP protocol ✅

## MCP Server Integration

The Stylize MCP Server provides Model Context Protocol (MCP) integration for AI agents and tools. The MCP server is built using FastMCP and exposes tools for image stylization.

### MCP Installation and Setup

To use the Stylize MCP Server in your MCP-compatible client (like Claude Desktop), add the following configuration:

#### For Claude Desktop

1. Create or update your `claude_desktop_config.json` file:

```json
{
  "mcpServers": {
    "stylize-mcp-server": {
      "command": "node",
      "args": [],
      "transport": {
        "type": "sse",
        "url": "https://stylize-mcp-server-997481449751.us-central1.run.app/mcp/sse"
      }
    }
  }
}
```

2. Restart Claude Desktop to load the new MCP server configuration.

#### For Local Development

When running the server locally (default port 8000), use:

```json
{
  "mcpServers": {
    "stylize-mcp-server-local": {
      "command": "node",
      "args": [],
      "transport": {
        "type": "sse",
        "url": "http://localhost:8000/mcp/sse"
      }
    }
  }
}
```

### Available MCP Tools

The MCP server provides the following **fully functional** tools for AI agents:

- **`stylize_image`**: Transform an uploaded image with a specific style
  - Parameters: `image_base64`, `style_id`, optional `user_prompt`, optional `project_context`
  - Returns: Publicly accessible stylized image URL, applied style, and final prompt used
  - **Status**: ✅ Working - generates and returns accessible image URLs

- **`list_styles`**: Get all available style options
  - Returns: List of 5 curated styles with id, name, and description
  - **Status**: ✅ Working - returns complete style catalog

- **`get_style_details`**: Get detailed information about a specific style
  - Parameters: `style_id`
  - Returns: Complete style information including prompt fragments
  - **Status**: ✅ Working - provides detailed style information

- **`generate_image_from_text`**: Generate an image from text description with styling
  - Parameters: `prompt`, `style_id`, optional `project_context`
  - Returns: Publicly accessible generated image URL, applied style, and final prompt used
  - **Status**: ✅ Working - creates new images from text prompts

### MCP Resources

- **`styles://catalog`**: Complete styles catalog as a JSON resource
  - **Status**: ✅ Working - provides full style database

### Available Styles

1. **Van Gogh** (`van_gogh`) - Post-impressionist paintings with bold, swirling brush strokes
2. **Pixel Art** (`pixel_art`) - Retro 8-bit video game aesthetic  
3. **Flat UI Icon** (`flat_ui_icon`) - Modern, minimalist interface design
4. **Neumorphic Button** (`neumorphic_button`) - Soft UI design with subtle shadows
5. **Abstract Geometric** (`abstract_geometric`) - Geometric patterns and shapes

### Production MCP Endpoint

The production MCP server is **live and accessible** at:
```
https://stylize-mcp-server-997481449751.us-central1.run.app/mcp/sse
```

**Tested and verified working with:**
- Claude Desktop (recommended)
- VS Code + GitHub Copilot 
- Cursor AI Editor
- Other MCP-compatible clients
