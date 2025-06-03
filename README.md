# Stylize MCP Server

[![CI/CD Pipeline](https://github.com/your-username/stylize-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/stylize-mcp/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/your-username/stylize-mcp/branch/main/graph/badge.svg)](https://codecov.io/gh/your-username/stylize-mcp)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://hub.docker.com/)
[![Google Cloud](https://img.shields.io/badge/cloud-google-orange.svg)](https://cloud.google.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-DALL·E%203-black.svg)](https://openai.com/)
[![Status](https://img.shields.io/badge/status-production-brightgreen.svg)](https://stylize-mcp-server-997481449751.us-central1.run.app/health)

## Overview

The Stylize MCP Server is a **fully operational** cloud-based service that transforms user-supplied images into multiple style-specific variants and provides AI agents with image generation capabilities via the Model Context Protocol (MCP). It leverages DALL·E 3 with a curated style bank, template-driven prompt engineering, content-safety filtering, and intelligent caching to deliver high-quality stylized images efficiently.

## ✅ Current Status: **FULLY FUNCTIONAL** + **WEB INTERFACE READY**

**🚀 Live Production Deployment:**
- **REST API**: https://stylize-mcp-server-997481449751.us-central1.run.app
- **Web Interface**: https://stylize-mcp-server-997481449751.us-central1.run.app/web/upgrade
- **MCP Endpoint**: https://stylize-mcp-server-997481449751.us-central1.run.app/mcp/sse
- **Free Trial**: **5 images immediately, no signup required!**
- **User Dashboard**: Complete credit purchase and account management
- **Health Status**: All services operational
- **Image Generation**: Working with public access URLs
- **MCP Integration**: Ready for Claude Desktop and other MCP clients

**🎯 Try It Now (No Account Needed!):**
```bash
# Single style:
curl -X POST https://stylize-mcp-server-997481449751.us-central1.run.app/stylize_image \
  -F "style_id=van_gogh" \
  -F "user_prompt=a beautiful landscape"

# Multiple styles (omit style_id for 4 random styles):
curl -X POST https://stylize-mcp-server-997481449751.us-central1.run.app/stylize_image \
  -F "user_prompt=a beautiful landscape"
```

## Completed Features

✅ **Complete Web Interface** - Trial upgrade forms and user dashboard  
✅ **Credit Purchase System** - One-click credit purchasing with 4 pricing tiers  
✅ **Freemium Trial System** - 5 free images, no signup required  
✅ **User Registration & Authentication** - Self-service account creation  
✅ **Subscription Tiers** - Free (100/mo), Pro (1K/mo), Enterprise (10K/mo)  
✅ **Credit System** - Pay-as-you-go pricing ($9.99-$99.99 packages)  
✅ **REST API endpoint for image stylization** (`POST /stylize_image`)  
✅ **MCP Server integration** with 6 tools including trial support  
✅ **Multi-style generation** - Generate 4 random styles in one request  
✅ **Curated style catalog** with 5 specialized styles  
✅ **DALL·E 3 integration** for high-quality image generation  
✅ **Content safety filtering** with Cloud Vision SafeSearch  
✅ **Public image access** via Google Cloud Storage  
✅ **Cost guardrails** with usage tracking and limits  
✅ **Infrastructure as code** deployed on Google Cloud Platform  
✅ **Comprehensive testing suite** and documentation

## 🚀 Getting Started (4 Ways to Use)

### **1. Web Interface (Recommended for Users)**
Experience the full platform with our user-friendly web interface:

**🎨 Trial Upgrade Page**: [https://stylize-mcp-server-997481449751.us-central1.run.app/web/upgrade](https://stylize-mcp-server-997481449751.us-central1.run.app/web/upgrade)
- Beautiful trial-to-account conversion form
- Shows remaining trial images and upgrade benefits
- Automatic session tracking and seamless user experience

**📊 User Dashboard**: [https://stylize-mcp-server-997481449751.us-central1.run.app/web/dashboard](https://stylize-mcp-server-997481449751.us-central1.run.app/web/dashboard)
- View credit balance, monthly usage, and subscription limits
- Purchase additional credits with one-click buttons
- Choose from 4 pricing tiers ($9.99 - $99.99)
- Professional responsive design for all devices

**✨ Features:**
- 🔐 Cookie-based authentication (no API knowledge needed)
- 📱 Mobile-responsive design
- 💳 Instant credit purchase (simplified - no payment processing)
- 🎯 Clear upgrade paths from trial to paid
- 🚀 Professional SaaS-quality interface

### **2. Anonymous Trial (API Access)**
Try immediately with **no account required** - get 5 free images:

```bash
# Generate with a specific style
curl -X POST https://stylize-mcp-server-997481449751.us-central1.run.app/stylize_image \
  -F "style_id=van_gogh" \
  -F "user_prompt=a serene mountain landscape"

# NEW: Generate 4 random styles (omit style_id) - perfect for exploring!
curl -X POST https://stylize-mcp-server-997481449751.us-central1.run.app/stylize_image \
  -F "user_prompt=a serene mountain landscape"

# Single style response:
{
  "original_id": "req-123",
  "style": "van_gogh",
  "stylized_image_url": "https://storage.googleapis.com/...",
  "trial_info": {
    "images_used": 1,
    "images_remaining": 4,
    "signup_message": "You have 4 free images remaining. Sign up for 100 free images per month!",
    "signup_url": "/auth/register"
  }
}

# Multiple styles response (4 images with different styles):
{
  "original_id": "req-124",
  "multiple_styles": true,
  "images": [
    {"style_id": "van_gogh", "style_name": "Van Gogh", "stylized_image_url": "..."},
    {"style_id": "pixel_art", "style_name": "Pixel Art", "stylized_image_url": "..."},
    {"style_id": "flat_ui_icon", "style_name": "Flat UI Icon", "stylized_image_url": "..."},
    {"style_id": "neumorphic_button", "style_name": "Neumorphic Button", "stylized_image_url": "..."}
  ],
  "total_images": 4,
  "trial_info": {
    "images_used": 5,
    "images_remaining": 0,
    "signup_message": "You have 0 free images remaining. Sign up for 100 free images per month!",
    "signup_url": "/auth/register"
  }
}
```

### **3. MCP Protocol (Claude Desktop)**
Use via Claude Desktop with trial support:

1. Add to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "stylize-server": {
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

2. Start trial in Claude:
```
"Start a trial session for image generation"
```

3. Generate images:
```
"Generate an image of a sunset with a specific style" 
# OR for multiple styles:
"Generate an image of a sunset using multiple random styles"
```
```
"Stylize this image in Van Gogh style using my trial session"
```

### **4. Full Account (API Access)**
Sign up for 100 free images per month:

```bash
# Create account
curl -X POST https://stylize-mcp-server-997481449751.us-central1.run.app/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "you@example.com",
    "password": "securepass123", 
    "first_name": "Your",
    "last_name": "Name"
  }'

# Generate API key
curl -H "Authorization: Bearer JWT_TOKEN" \
  -X POST https://stylize-mcp-server-997481449751.us-central1.run.app/user/api-keys \
  -d '{"name": "My Integration"}'
```

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
# Authentication: AUTH_ENABLED, API_KEYS_SECRET_PATH, DEV_API_KEY
# Optional: REDIS_HOST, REDIS_PORT for caching
```

### Authentication Configuration

The Stylize MCP Server now includes **API key authentication** for all endpoints:

#### Environment Variables
```bash
# Authentication settings
AUTH_ENABLED=true                    # Enable/disable authentication (default: true)
AUTH_DEV_BYPASS=false               # Allow bypassing auth in development (default: false)
API_KEYS_SECRET_PATH=api-keys       # Secret Manager path for API keys (default: api-keys)
DEV_API_KEY=your-dev-key-here       # Development API key (only used when AUTH_DEV_BYPASS=true)
```

#### Development Setup
For local development, you can either:

1. **Bypass authentication** (quickest for testing):
```bash
export AUTH_DEV_BYPASS=true
export DEV_API_KEY=test-key-123
```

2. **Use production-like authentication** by creating API keys in Google Cloud Secret Manager

#### Production Setup
API keys are managed in Google Cloud Secret Manager as JSON:
```json
{
  "key-abc123": {
    "key_id": "key-abc123",
    "name": "Production Client",
    "hashed_key": "sha256_hash_of_actual_key",
    "is_active": true,
    "permissions": ["stylize", "styles", "mcp"],
    "created_at": "2024-01-01T00:00:00Z"
  }
}
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

**REST API (Fully Operational with Freemium Trial):**

#### **🆓 Trial Endpoints (No Authentication Required)**
- `POST /stylize_image`: Generate stylized images with trial support ✅
  - **Authentication**: Optional - works without auth for 5 free images
  - **Trial Response**: Includes usage info and upgrade prompts
- `GET /trial/status`: Check anonymous trial usage ✅
  - **Authentication**: None required
- `GET /pricing/packages`: View credit packages and pricing ✅
  - **Authentication**: None required

#### **👤 User Endpoints** 
- `POST /auth/register`: Register new user account ✅
- `POST /auth/login`: User login (returns JWT) ✅
- `POST /trial/convert`: Convert trial session to account ✅
- `GET /user/profile`: Get user profile ✅
- `GET /user/usage`: Get usage stats and limits ✅
- `GET /user/credits`: Get user credit balance ✅
- `POST /user/purchase-credits`: Purchase credit packages ✅
- `GET /user/dashboard`: Complete user dashboard data ✅
- `POST /user/api-keys`: Create API key for current user ✅

#### **🌐 Web Interface Endpoints**
- `GET /web/upgrade`: Trial upgrade form page ✅
- `POST /web/trial/upgrade`: Process trial conversion ✅
- `GET /web/dashboard`: User dashboard with credit purchase ✅
- `POST /web/purchase`: Process credit purchase via form ✅
- `GET /web/logout`: User logout ✅

#### **🔧 Admin Endpoints**
- `POST /admin/api-keys`: Create API key (admin) ✅
- `GET /admin/api-keys`: List all API keys ✅
- `PATCH /admin/api-keys/{key_id}`: Update API key ✅
- `DELETE /admin/api-keys/{key_id}`: Deactivate API key ✅

#### **📊 Public Endpoints**
- `GET /styles`: List available styles ✅
  - **Authentication**: Required for authenticated users, works in trial mode
- `GET /health`: Server health check ✅
  - **Authentication**: Public (no authentication required)
- `GET /docs`: OpenAPI documentation ✅
  - **Authentication**: Public (no authentication required)

**MCP Protocol Endpoints:**
- `/mcp/sse`: Server-Sent Events transport for MCP clients ✅
  - **Authentication**: API key with `mcp` permission OR trial session
- `/mcp`: JSON-RPC endpoint for MCP protocol ✅
  - **Authentication**: API key with `mcp` permission OR trial session

### Using Authenticated Endpoints

#### REST API
Include your API key in the Authorization header:
```bash
curl -H "Authorization: Bearer your-api-key-here" \
     -X POST https://stylize-mcp-server-997481449751.us-central1.run.app/stylize_image \
     -F "style_id=van_gogh" \
     -F "user_prompt=a beautiful landscape"
```

#### MCP Tools
Include your API key as a parameter in tool calls:
```python
result = await stylize_image(
    image_base64="...",
    style_id="van_gogh",
    api_key="your-api-key-here"
)
```

### Available Permissions
- **`stylize`**: Access to image generation and stylization endpoints
- **`styles`**: Access to style catalog and management endpoints  
- **`mcp`**: Access to all MCP tools and resources
- **`admin`**: Full access to all endpoints and operations

## API Key Management

### How Users Get API Keys

**For Public SaaS Customers (Recommended):**

#### Self-Service Registration & API Key Generation
1. **Sign up for free account:**
```bash
curl -X POST https://stylize-mcp-server.com/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com", 
    "password": "securepass123",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

2. **Generate your own API keys:**
```bash
curl -H "Authorization: Bearer JWT_TOKEN" \
  -X POST https://stylize-mcp-server.com/user/api-keys \
  -d '{"name": "My App Integration"}'
```

3. **Start using with automatic usage tracking and limits!**

#### Subscription Tiers
- **🆓 FREE**: 100 images/month, 1 API key, basic styles
- **💎 PRO ($19/mo)**: 1,000 images/month, 5 API keys, all styles + MCP
- **🚀 ENTERPRISE ($99/mo)**: 10,000 images/month, unlimited keys, priority support

---

**For Enterprise/Admin Users:**

Users can obtain API keys through these methods:

#### Method 1: Admin API Endpoints
Administrators with `admin` permission can create keys for users:

```bash
# Create a new API key
curl -H "Authorization: Bearer admin-api-key" \
     -X POST https://stylize-mcp-server-997481449751.us-central1.run.app/admin/api-keys \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Production Client",
       "permissions": ["stylize", "styles", "mcp"]
     }'

# Response includes the actual key (shown only once)
{
  "key_id": "key-abc123",
  "name": "Production Client", 
  "api_key": "64-character-hex-key-here",
  "permissions": ["stylize", "styles", "mcp"],
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### Method 2: CLI Utility
For local/development environments, use the included CLI:

```bash
# Create a new API key
python manage_api_keys.py create "Production Client" --permissions stylize styles mcp

# List all existing keys
python manage_api_keys.py list

# Deactivate a key
python manage_api_keys.py deactivate key-abc123

# Get help and show available permissions
python manage_api_keys.py info
```

### Admin API Endpoints

**`POST /admin/api-keys`** - Create new API key
- Requires: `admin` permission
- Body: `{"name": "string", "permissions": ["stylize", "styles"]}`
- Returns: Complete key info including the actual API key

**`GET /admin/api-keys`** - List all API keys  
- Requires: `admin` permission
- Returns: Array of key info (without actual keys)

**`PATCH /admin/api-keys/{key_id}`** - Update key properties
- Requires: `admin` permission  
- Body: `{"is_active": true, "permissions": ["stylize"]}`

**`DELETE /admin/api-keys/{key_id}`** - Deactivate key
- Requires: `admin` permission
- Deactivates but doesn't delete (for audit trails)

### New SaaS Endpoints

**User Authentication:**
- **`POST /auth/register`** - Register new user account
- **`POST /auth/login`** - User login (returns JWT)
- **`GET /user/profile`** - Get user profile
- **`GET /user/usage`** - Get usage stats and limits

**Self-Service API Keys:**
- **`POST /user/api-keys`** - Create API key for current user
- **`GET /user/api-keys`** - List user's API keys
- **`DELETE /user/api-keys/{key_id}`** - Revoke API key

### Bootstrap Process

**For SaaS Customers (Public):**
1. Sign up at `/auth/register` 
2. Get free tier automatically
3. Generate API keys immediately
4. Upgrade subscription as needed

**For Enterprise/Admin Setup:**

1. **Create the first admin key** using the CLI (requires server access):
```bash
# On the server or with appropriate GCP credentials
python manage_api_keys.py create "First Admin" --permissions admin stylize styles mcp
```

2. **Use that admin key** to create additional keys via the API endpoints

3. **For development**, use the bypass mode:
```bash
export AUTH_DEV_BYPASS=true
export DEV_API_KEY=your-dev-key-here
# Now the dev key has admin permissions
```

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

#### **🆓 Trial Tools (No Authentication Required)**

- **`start_trial_session`**: Start anonymous trial session
  - Parameters: None
  - Returns: Session ID, 5 free images, upgrade options, instructions
  - **Authentication**: None required
  - **Status**: ✅ Working - instant trial access

- **`check_trial_status`**: Check trial usage
  - Parameters: `session_id`
  - Returns: Images used/remaining, trial status, upgrade options
  - **Authentication**: None required
  - **Status**: ✅ Working - real-time usage tracking

#### **🎨 Image Generation Tools**

- **`stylize_image`**: Transform an uploaded image with a specific style OR generate 4 random styles
  - Parameters: `image_base64`, `style_id` (optional - omit for 4 random styles), **either** `api_key` **or** `session_id`, optional `user_prompt`, optional `project_context`
  - Returns: 
    - **Single style** (when style_id provided): Stylized image URL, applied style, prompt used
    - **Multiple styles** (when style_id omitted): Array of 4 images with different random styles
    - **Trial info** (if using trial): Usage tracking and upgrade options
  - **Authentication**: API key with `mcp` permission **OR** trial session ID
  - **Status**: ✅ Working - supports both authenticated and trial usage, single and multi-style generation

- **`generate_image_from_text`**: Generate an image from text description with specific style OR 4 random styles
  - Parameters: `prompt`, `style_id` (optional - omit for 4 random styles), **either** `api_key` **or** `session_id`, optional `project_context`
  - Returns:
    - **Single style** (when style_id provided): Generated image URL, applied style, prompt used
    - **Multiple styles** (when style_id omitted): Array of 4 images with different random styles
    - **Trial info** (if using trial): Usage tracking and upgrade options
  - **Authentication**: API key with `mcp` permission **OR** trial session ID
  - **Status**: ✅ Working - supports both authenticated and trial usage, single and multi-style generation

#### **📋 Information Tools**

- **`list_styles`**: Get all available style options
  - Parameters: `api_key` (required for authenticated access)
  - Returns: List of 5 curated styles with id, name, and description
  - **Authentication**: Requires valid API key with `mcp` permission
  - **Status**: ✅ Working - returns complete style catalog

- **`get_style_details`**: Get detailed information about a specific style
  - Parameters: `style_id`, `api_key`
  - Returns: Complete style information including prompt fragments
  - **Authentication**: Requires valid API key with `mcp` permission
  - **Status**: ✅ Working - provides detailed style information

### MCP Resources

- **`styles://catalog`**: Complete styles catalog as a JSON resource
  - Parameters: `api_key`
  - **Authentication**: Requires valid API key with `mcp` permission
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
