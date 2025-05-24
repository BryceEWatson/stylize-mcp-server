# Stylize MCP Server - Quick Start Guide

## 🚀 Ready to Use - No Setup Required!

The Stylize MCP Server is **live and fully operational**. Get started in minutes:

## Option 1: Claude Desktop (Recommended)

### Step 1: Download Claude Desktop
- Get Claude Desktop from [claude.ai](https://claude.ai/download)

### Step 2: Configure MCP Server
Create or edit the configuration file:

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`  
**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "stylize-mcp-server": {
      "transport": {
        "type": "sse",
        "url": "https://stylize-mcp-server-997481449751.us-central1.run.app/mcp/sse"
      }
    }
  }
}
```

### Step 3: Restart Claude Desktop

### Step 4: Start Creating!
Try these prompts:
- "Generate a pixel art image of a robot"
- "Create a Van Gogh style painting of a sunset"
- "Make a flat UI icon for a music app"
- "What image styles are available?"

## Option 2: Direct REST API

### Test the Service
```bash
# Check if service is running
curl https://stylize-mcp-server-997481449751.us-central1.run.app/health

# Generate an image
curl -X POST https://stylize-mcp-server-997481449751.us-central1.run.app/stylize_image \
  -F "style_id=van_gogh" \
  -F "user_prompt=a friendly cat in a garden"

# Get available styles
curl https://stylize-mcp-server-997481449751.us-central1.run.app/styles
```

## Available Styles

| Style ID | Name | Description |
|----------|------|-------------|
| `van_gogh` | Van Gogh | Post-impressionist paintings with bold, swirling brush strokes |
| `pixel_art` | Pixel Art | Retro 8-bit video game aesthetic |
| `flat_ui_icon` | Flat UI Icon | Modern, minimalist interface design |
| `neumorphic_button` | Neumorphic Button | Soft UI design with subtle shadows |
| `abstract_geometric` | Abstract Geometric | Geometric patterns and shapes |

## MCP Tools Available

- **`stylize_image`** - Transform images with specific styles
- **`generate_image_from_text`** - Create images from text descriptions  
- **`list_styles`** - Get all available styles
- **`get_style_details`** - Get detailed style information

## Need Help?

- **API Documentation**: https://stylize-mcp-server-997481449751.us-central1.run.app/docs
- **Testing Guide**: See `docs/TESTING_GUIDE.md`
- **Full Documentation**: See `README.md`

---

**That's it!** The service is ready to use - no installation, configuration, or API keys needed on your end.