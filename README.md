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

🌟 **Interactive Demo**: [https://stylize-mcp-server-997481449751.us-central1.run.app/web/demo](https://stylize-mcp-server-997481449751.us-central1.run.app/web/demo)
- **Drag & drop image upload** or **text-to-image generation**
- **Real-time credit tracking** with 5 free images
- **Try all 6 artistic styles** including "Surprise Me" for 4 random styles
- **Learn MCP integration** with step-by-step Claude Desktop setup

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
✅ **Advanced Trial Abuse Prevention** - Multi-layered security system to prevent trial exploitation  
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

## 🚀 Getting Started (5 Ways to Use)

### **1. Interactive Demo (Recommended for First-Time Users)**
Try the service instantly with no account required:

**🌟 Demo Page**: [https://stylize-mcp-server-997481449751.us-central1.run.app/web/demo](https://stylize-mcp-server-997481449751.us-central1.run.app/web/demo)
- **🎨 Real-time image stylization** - Upload images or enter text prompts
- **🎲 "Surprise Me" feature** - Generate 4 random artistic styles at once
- **📊 Live credit tracking** - See your 5 free images update in real-time
- **🤖 MCP integration guide** - Step-by-step Claude Desktop setup instructions
- **📱 Mobile-friendly interface** - Works perfectly on phones and tablets

### **2. Web Interface (For Account Management)**
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

### **3. Anonymous Trial (API Access)**
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

### **4. MCP Protocol (Claude Desktop)**
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

### **5. Full Account (API Access)**
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

## 🛡️ Trial Abuse Prevention System

The Stylize MCP Server includes a sophisticated **multi-layered abuse prevention system** to ensure fair trial usage while maintaining a seamless user experience. This system operates transparently, requiring no additional user interaction.

### Security Features

#### **🔍 Device Fingerprinting**
- **Client-side fingerprinting** using canvas, WebGL, screen resolution, and font detection
- **Server-side analysis** of headers, IP geolocation, and connection patterns
- **Spoofing detection** with entropy analysis and consistency checks
- **Cross-session tracking** to prevent multiple trial abuse

#### **🌐 VPN & Proxy Detection**
- **Multi-API integration** with IPQualityScore and ProxyCheck.io for real-time VPN detection
- **Datacenter hosting detection** using ASN analysis and GeoIP database
- **Known VPN range checking** against curated IP range databases
- **Risk scoring** based on connection source and patterns

#### **🤖 Behavioral Analysis**
- **Automation detection** using timing patterns, request sequences, and user agent analysis
- **Mouse movement tracking** to distinguish human vs. bot interactions
- **Request pattern analysis** for detecting scripted behavior
- **Progressive challenge system** based on risk assessment

#### **⚡ Advanced Rate Limiting**
- **Multi-dimensional limits**: Per-IP, per-device, per-session, and global rate controls
- **Sliding window algorithms** for precise usage tracking
- **Risk-based throttling** with higher limits for low-risk users
- **Burst protection** to prevent rapid trial exhaustion

#### **📊 Real-time Risk Scoring**
- **ML-based assessment** combining device, location, and behavioral signals
- **Dynamic threshold adjustment** based on threat patterns
- **Confidence scoring** to minimize false positives
- **Adaptive security** that learns from abuse patterns

#### **🚨 Abuse Monitoring & Alerting**
- **Real-time event logging** with structured abuse event tracking
- **Pattern detection** for identifying coordinated abuse attempts
- **Automatic response** including temporary restrictions and challenges
- **Admin dashboards** for monitoring security metrics

### Configuration

The security system is **configurable via environment variables**:

```bash
# Security System
SECURITY_ENABLED=true                    # Enable abuse prevention (default: false)
HIGH_RISK_THRESHOLD=0.7                 # Risk score threshold for challenges (default: 0.7)
FINGERPRINTING_ENABLED=true            # Enable device fingerprinting (default: true)

# VPN Detection
VPN_DETECTION_PAID_APIS=true           # Enable premium VPN detection APIs (default: false)
IPQUALITYSCORE_API_KEY=your_key        # IPQualityScore API key (optional)
PROXYCHECK_API_KEY=your_key            # ProxyCheck.io API key (optional)

# Rate Limiting
TRIAL_CREATION_PER_IP=5                # Max trials per IP per day (default: 5)
TRIAL_CREATION_PER_DEVICE=3            # Max trials per device per day (default: 3)
IMAGE_GENERATION_PER_SESSION=5         # Max images per session (default: 5)
GLOBAL_DAILY_LIMIT=10000               # Global daily image limit (default: 10000)

# CAPTCHA Challenges
RECAPTCHA_SITE_KEY=your_site_key       # reCAPTCHA site key (optional)
RECAPTCHA_SECRET_KEY=your_secret       # reCAPTCHA secret key (optional)
HCAPTCHA_SITE_KEY=your_site_key        # hCAPTCHA site key (optional)
HCAPTCHA_SECRET_KEY=your_secret        # hCAPTCHA secret key (optional)
```

### Graceful Degradation

The system is designed for **backward compatibility** and **graceful degradation**:

- **Works without configuration**: Falls back to basic IP-based tracking
- **Optional API integrations**: VPN detection works with free tier, premium APIs enhance accuracy
- **Progressive enhancement**: Additional security layers activate as services are configured
- **Zero user friction**: Security operates transparently without impacting legitimate users

### Privacy & Compliance

- **Minimal data collection**: Only technical metadata required for abuse prevention
- **No personal information**: Device fingerprints are cryptographic hashes, not personal data
- **GDPR compliance**: Anonymous technical identifiers with automatic expiration
- **Transparency**: Security measures are documented and user-visible when triggered

### Detailed Security Documentation

For comprehensive security configuration, deployment guides, and troubleshooting:

📚 **[Security Configuration Guide](docs/SECURITY_CONFIGURATION.md)** - Complete reference for configuring and deploying the abuse prevention system

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
# Security: SECURITY_ENABLED, HIGH_RISK_THRESHOLD, VPN detection keys
# Optional: REDIS_HOST, REDIS_PORT for caching
```

### Authentication Configuration

The Stylize MCP Server now includes **API key authentication** for all endpoints:

#### Environment Variables

**Core Settings:**
```bash
# Authentication settings
AUTH_ENABLED=true                    # Enable/disable authentication (default: true)
AUTH_DEV_BYPASS=false               # Allow bypassing auth in development (default: false)
API_KEYS_SECRET_PATH=api-keys       # Secret Manager path for API keys (default: api-keys)
DEV_API_KEY=your-dev-key-here       # Development API key (only used when AUTH_DEV_BYPASS=true)

# Security & Abuse Prevention
SECURITY_ENABLED=true               # Enable comprehensive trial abuse prevention (default: false)
HIGH_RISK_THRESHOLD=0.7             # Risk score threshold for challenges (default: 0.7)
FINGERPRINTING_ENABLED=true        # Enable device fingerprinting (default: true)
```

**Optional Security Enhancements:**
```bash
# VPN & Proxy Detection
VPN_DETECTION_PAID_APIS=true       # Enable premium VPN detection APIs (default: false)
IPQUALITYSCORE_API_KEY=your_key    # IPQualityScore API key (optional)
PROXYCHECK_API_KEY=your_key        # ProxyCheck.io API key (optional)

# Rate Limiting
TRIAL_CREATION_PER_IP=5            # Max trial sessions per IP per day (default: 5)
TRIAL_CREATION_PER_DEVICE=3        # Max trial sessions per device per day (default: 3)
GLOBAL_DAILY_LIMIT=10000           # Global daily image generation limit (default: 10000)

# CAPTCHA Integration
RECAPTCHA_SITE_KEY=your_site_key   # Google reCAPTCHA site key (optional)
RECAPTCHA_SECRET_KEY=your_secret   # Google reCAPTCHA secret key (optional)
HCAPTCHA_SITE_KEY=your_site_key    # hCAPTCHA site key (optional)
HCAPTCHA_SECRET_KEY=your_secret    # hCAPTCHA secret key (optional)
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
- `GET /web/demo`: Interactive demo page with trial credits ✅
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

#### **🛡️ Security & Monitoring Endpoints**
- `GET /admin/security/metrics`: Security metrics and abuse statistics (admin) ✅
- `POST /admin/security/report-abuse`: Report manual abuse event (admin) ✅
- `POST /security/challenge`: Force CAPTCHA challenge for session ✅
- `GET /static/js/fingerprint.js`: Client-side device fingerprinting library ✅

**Security Headers Added to Responses:**
- `X-Security-Risk-Score`: Current request risk assessment (0.0-1.0)
- `X-Rate-Limit-Remaining`: Remaining requests in current window
- `X-Device-Fingerprint`: Device fingerprinting status
- `X-VPN-Detection`: VPN/proxy detection result

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

## MCP Server Integration 🤖

The Stylize MCP Server is designed to **enhance AI assistants** with professional image generation capabilities through natural conversation. Rather than exposing technical APIs, it enables AI assistants like Claude to seamlessly integrate image creation into conversational workflows.

### 🎯 AI Assistant Experience

**For Users Talking to AI Assistants:**
- **Natural Requests**: "Make this photo look like a Van Gogh painting"
- **Style Exploration**: "Show me this image in different artistic styles"  
- **Creative Guidance**: "Create a logo for my coffee shop"
- **Seamless Trials**: Start with 5 free images, no account needed
- **Progressive Enhancement**: AI guides from trial → free account → paid credits

**For AI Assistants:**
- **Intelligent Tool Selection**: Automatically choose single vs multi-style generation
- **Trial Management**: Handle usage limits gracefully with upgrade suggestions
- **Error Recovery**: Convert technical errors into helpful user guidance
- **Context Awareness**: Incorporate brand guidelines and project context

### MCP Installation and Setup

#### For Claude Desktop (Recommended)

1. **Add to your `claude_desktop_config.json`:**

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

2. **Restart Claude Desktop** to load the new MCP server

3. **Start Conversing!** Claude will automatically discover and use the tools:

**Example Conversation:**
```
User: "Can you help me create some artistic versions of this photo?"

Claude: "I'd be happy to help! Let me start a trial session and create some artistic interpretations of your photo."

[Claude calls start_trial_session() and stylize_image() with multiple styles]

Claude: "I've created 4 different artistic styles for your photo:
• Van Gogh: Bold, swirling brush strokes with vibrant colors
• Pixel Art: Retro 8-bit gaming aesthetic  
• Flat UI: Clean, modern minimalist design
• Neumorphic: Soft, dimensional interface style

Which style appeals to you most? You have 1 more trial image remaining, or I can help you sign up for 100 free images per month!"
```

#### For Other MCP Clients

**Local Development:**
```json
{
  "mcpServers": {
    "stylize-server-local": {
      "transport": {
        "type": "sse",
        "url": "http://localhost:8000/mcp/sse"
      }
    }
  }
}
```

**Custom Integration:**
```python
import mcp_client

# Connect to the MCP server
client = mcp_client.connect("https://stylize-mcp-server-997481449751.us-central1.run.app/mcp")

# AI assistants can now use the tools naturally
trial = await client.call_tool("start_trial_session", {})
result = await client.call_tool("stylize_image", {
    "image_base64": user_uploaded_image,
    "session_id": trial["session_id"]
    # Omitting style_id generates 4 random styles
})
```

### 🛠️ AI Assistant Tools

The MCP server provides tools that AI assistants use **behind the scenes** to help users with image creation. Users never see these technical details - they just have natural conversations!

#### **🚀 Trial Session Management**

**`start_trial_session`** - Begin anonymous trial
- **AI Assistant Use**: "Let me start a free trial for you to explore image generation"
- **User Experience**: Instant access to 5 free images without signup
- **Returns**: Session ID for tracking, available images, upgrade information
- **Status**: ✅ Working - zero-friction trial start

**`check_trial_status`** - Monitor trial usage  
- **AI Assistant Use**: Proactively check remaining images before generation
- **User Experience**: "You have 2 trial images remaining" with upgrade suggestions
- **Returns**: Real-time usage tracking and conversion opportunities
- **Status**: ✅ Working - intelligent usage guidance

#### **🎨 Intelligent Image Generation**

**`stylize_image`** - Transform uploaded images
- **AI Assistant Use**: 
  - **Single Style**: "I'll apply Van Gogh's style to your photo"
  - **Multi-Style**: "Let me show you 4 different artistic interpretations"
- **User Experience**: Upload image → Get styled results with conversational explanation
- **Smart Behavior**: Omit `style_id` for automatic 4-style exploration
- **Authentication**: Works with trial sessions OR API keys
- **Status**: ✅ Working - seamless image transformation

**`generate_image_from_text`** - Create images from descriptions
- **AI Assistant Use**:
  - **Guided Creation**: "I'll create a logo based on your description"
  - **Style Variety**: "Let me generate this in multiple styles for you to choose"
- **User Experience**: Describe vision → Get professional results with style explanations
- **Smart Behavior**: Automatic style selection based on context
- **Authentication**: Works with trial sessions OR API keys  
- **Status**: ✅ Working - intelligent text-to-image generation

#### **🎯 Style Discovery & Guidance**

**`list_styles`** - Discover available styles
- **AI Assistant Use**: "Here are the artistic styles I can create for you..."
- **User Experience**: Conversational style explanations with examples
- **Returns**: 5 curated professional styles with descriptions
- **Status**: ✅ Working - style education and selection

**`get_style_details`** - Deep style information
- **AI Assistant Use**: Provide rich context about chosen styles
- **User Experience**: "Van Gogh style uses bold, swirling brush strokes that..."
- **Returns**: Complete style context for informed decisions
- **Status**: ✅ Working - style expertise on demand

### 💡 How AI Assistants Use These Tools

#### **Discovery & Onboarding Pattern**
```
User: "What can you do with images?"

AI Assistant Process:
1. start_trial_session() → Get session for demos
2. list_styles() → Learn available options  
3. Present capabilities conversationally with examples

User Experience:
"I can transform your images in 5 artistic styles: Van Gogh's bold strokes, retro pixel art, modern flat design, soft neumorphic interfaces, and geometric abstraction. Want to try one with your own image?"
```

#### **Smart Generation Pattern**
```
User: "Make this photo artistic"

AI Assistant Process:
1. check_trial_status() → Verify available images
2. stylize_image(no style_id) → Generate 4 random styles
3. Present results with style education

User Experience:
"I've created 4 artistic interpretations:
• Van Gogh: [image] - Bold, emotional brush work
• Pixel Art: [image] - Nostalgic 8-bit charm  
• Flat UI: [image] - Clean, modern simplicity
• Neumorphic: [image] - Soft, tactile interface

Which direction speaks to you? I can refine any of these further!"
```

#### **Conversion & Growth Pattern**
```
User: "Create another image"

AI Assistant Process:
1. check_trial_status() → Sees trial exhausted
2. Present upgrade options conversationally

User Experience:
"You've explored all 5 trial images! Ready to unlock more creativity? 
🆓 Sign up for 100 free images per month, or
💎 Get unlimited access with credit packages
I can help you sign up right now!"
```

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
