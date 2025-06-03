# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Running the Application
```bash
# Activate virtual environment first
python -m venv venv
source venv/bin/activate  # On Unix/macOS
venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt

# Run server locally
uvicorn app.main:app --reload

# Run with specific port
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

### 🆓 Freemium Trial System & Web Interface
The server now supports **anonymous trial usage** with a complete web interface for user conversion and credit purchases!

#### Web Interface for Users
```bash
# Trial Upgrade Web Page (users can create accounts)
https://stylize-mcp-server-997481449751.us-central1.run.app/web/upgrade

# User Dashboard (authenticated users)
https://stylize-mcp-server-997481449751.us-central1.run.app/web/dashboard

# Key Web Endpoints:
# GET /web/upgrade - Trial upgrade form with session tracking
# POST /web/trial/upgrade - Process trial conversion
# GET /web/dashboard - User dashboard with credits and purchase options
# POST /web/purchase - Credit purchase processing
# GET /web/logout - User logout
```

#### Testing Trial Access via API
```bash
# Test anonymous trial usage with specific style (no auth needed)
curl -X POST http://localhost:8080/stylize_image \
  -F "style_id=van_gogh" \
  -F "user_prompt=a beautiful sunset"

# Response for single style:
{
  "original_id": "req-123",
  "style": "van_gogh",
  "stylized_image_url": "https://...",
  "trial_info": {
    "images_used": 1,
    "images_remaining": 4,
    "signup_message": "You have 4 free images remaining. Sign up for 100 free images per month!",
    "signup_url": "/auth/register"
  }
}

# Test with multiple random styles (omit style_id)
curl -X POST http://localhost:8080/stylize_image \
  -F "user_prompt=a beautiful sunset"

# Response for multiple styles (generates 4 random styles):
{
  "original_id": "req-124",
  "multiple_styles": true,
  "images": [
    {
      "style_id": "van_gogh",
      "style_name": "Van Gogh",
      "stylized_image_url": "https://...",
      "prompt_used": "a beautiful sunset, in the style of Vincent van Gogh..."
    },
    {
      "style_id": "pixel_art",
      "style_name": "Pixel Art",
      "stylized_image_url": "https://...",
      "prompt_used": "a beautiful sunset, as pixel art..."
    },
    {
      "style_id": "flat_ui_icon",
      "style_name": "Flat UI Icon",
      "stylized_image_url": "https://...",
      "prompt_used": "a beautiful sunset, as a minimalist flat design..."
    },
    {
      "style_id": "neumorphic_button",
      "style_name": "Neumorphic Button",
      "stylized_image_url": "https://...",
      "prompt_used": "a beautiful sunset, as a neumorphic UI element..."
    }
  ],
  "total_images": 4,
  "trial_info": {
    "images_used": 5,
    "images_remaining": 0,
    "signup_message": "You have 0 free images remaining. Sign up for 100 free images per month!",
    "signup_url": "/auth/register"
  }
}

# Check trial status
curl http://localhost:8080/trial/status

# View pricing packages
curl http://localhost:8080/pricing/packages

# Convert trial to user account
curl -X POST http://localhost:8080/trial/convert \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "trial-abc123",
    "email": "user@example.com",
    "password": "password123",
    "first_name": "John",
    "last_name": "Doe",
    "company": "Example Corp"
  }'
```

### 💳 User Credit System
Authenticated users have access to a credit-based system for purchasing additional image generations.

#### User Credit Management
```bash
# Get user credit balance (requires authentication)
curl -H "Authorization: Bearer user-jwt-token" \
     http://localhost:8080/user/credits

# Purchase credits (requires authentication)
curl -H "Authorization: Bearer user-jwt-token" \
     -X POST http://localhost:8080/user/purchase-credits \
     -H "Content-Type: application/json" \
     -d '{"package_id": "starter"}'

# Get user dashboard with complete information
curl -H "Authorization: Bearer user-jwt-token" \
     http://localhost:8080/user/dashboard
```

#### Available Credit Packages
- **Starter Pack**: 50 credits + 5 bonus credits for $9.99
- **Popular Pack**: 200 credits + 25 bonus credits for $29.99 ⭐ Most Popular
- **Pro Pack**: 500 credits + 75 bonus credits for $59.99
- **Enterprise Pack**: 1000 credits + 200 bonus credits for $99.99
```

### Authentication Configuration
The server supports API key authentication for all endpoints (API and MCP).

#### Environment Variables
```bash
# Authentication settings
AUTH_ENABLED=true                    # Enable/disable authentication (default: true)
AUTH_DEV_BYPASS=false               # Allow bypassing auth in development (default: false)
API_KEYS_SECRET_PATH=api-keys       # Secret Manager path for API keys (default: api-keys)
DEV_API_KEY=your-dev-key-here       # Development API key (only used when AUTH_DEV_BYPASS=true)
```

#### API Key Management
API keys are stored in Google Cloud Secret Manager as JSON:
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

#### Creating API Keys

**Method 1: Admin API Endpoints**
```bash
# Create a new API key (requires admin permission)
curl -H "Authorization: Bearer admin-api-key" \
     -X POST http://localhost:8080/admin/api-keys \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Production Client",
       "permissions": ["stylize", "styles", "mcp"]
     }'

# List all API keys
curl -H "Authorization: Bearer admin-api-key" \
     -X GET http://localhost:8080/admin/api-keys

# Deactivate an API key
curl -H "Authorization: Bearer admin-api-key" \
     -X DELETE http://localhost:8080/admin/api-keys/key-abc123
```

**Method 2: CLI Utility**
```bash
# Create a new API key
python manage_api_keys.py create "Production Client" --permissions stylize styles mcp

# List all API keys
python manage_api_keys.py list

# Deactivate an API key
python manage_api_keys.py deactivate key-abc123

# Show available permissions and config
python manage_api_keys.py info
```

#### Using API Keys
**REST API**: Include in Authorization header
```bash
# Single style
curl -H "Authorization: Bearer your-api-key-here" \
     -X POST http://localhost:8080/stylize_image \
     -F "style_id=van_gogh" \
     -F "user_prompt=a beautiful landscape"

# Multiple random styles (omit style_id for 4 random styles)
curl -H "Authorization: Bearer your-api-key-here" \
     -X POST http://localhost:8080/stylize_image \
     -F "user_prompt=a beautiful landscape"
```

**MCP Tools**: Use API key OR trial session
```python
# Single style with API key (authenticated)
result = await stylize_image(
    image_base64="...",
    style_id="van_gogh",
    api_key="your-api-key-here"
)

# Multiple random styles with API key (omit style_id)
result = await stylize_image(
    image_base64="...",
    api_key="your-api-key-here"
)
# Returns: {"multiple_styles": true, "images": [...], "total_images": 4}

# With trial session (anonymous)
trial = await start_trial_session()
result = await stylize_image(
    image_base64="...",
    style_id="van_gogh",  # or omit for 4 random styles
    session_id=trial["session_id"]
)
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_main.py

# Run tests with verbose output (default from pytest.ini)
pytest -v

# Run tests and show output
pytest -s

# Run specific test by name
pytest tests/test_main.py::test_health_endpoint

# Run tests in parallel (if pytest-xdist installed)
pytest -n auto
```

### Docker
```bash
# Build Docker image
docker build -t stylize-mcp-server .

# Run Docker container
docker run -p 8080:8080 stylize-mcp-server
```

### Infrastructure Management
```bash
# From the infra/ directory:
terraform init
terraform plan
terraform apply
```

## High-Level Architecture

### Core Services Architecture
The application is a FastAPI-based server that provides:
1. **REST API** for image stylization (`/stylize_image`), style management (`/styles`), user management, and health checks
2. **Web Interface** for trial upgrade (`/web/upgrade`) and user dashboard (`/web/dashboard`) with credit purchasing
3. **MCP Server** endpoint at `/mcp` for AI agent integration via FastMCP
4. **User Management System** with trial sessions, user accounts, credit purchasing, and JWT authentication
5. **Two-stage image generation pipeline**:
   - Context analysis using GPT-4V when reference images are provided
   - Prompt generation and image creation using DALL·E 3
   - Results are cached in Redis and stored in GCS

### Service Dependencies
- **OpenAI API**: GPT-4V for analysis, DALL·E 3 for generation
- **Google Cloud Storage**: Image persistence and public access
- **Firestore**: User accounts, trial sessions, credit balances, usage tracking, and API key storage
- **Cloud Vision API**: SafeSearch content filtering
- **Redis (Memorystore)**: Response caching (optional, uses in-memory fallback)
- **Secret Manager**: OpenAI API key and admin credentials storage

### Key Implementation Details
- The application supports context-aware generation through a `ProjectContext` model for brand consistency
- **Multi-Style Generation**: When no `style_id` is provided, the system automatically generates 4 images with randomly selected styles
- **Usage Tracking**: Multiple style generation counts as multiple image usage (4x for random styles)
- Image generation includes automatic SafeSearch filtering for uploaded content
- Cost controls are implemented via daily global caps and per-user quotas tracked in Firestore
- The style catalog currently uses a JSON file (`app/styles.json`) with 5 predefined styles: van_gogh, pixel_art, flat_ui_icon, neumorphic_button, glassmorphic_card

### Manual Setup Requirements
After Terraform deployment:
1. OpenAI API key must be manually added to Secret Manager
2. Cloud Build GitHub connection requires manual configuration
3. Budget alerts need manual setup in GCP Console

### Testing Strategy
The test suite covers all major components:
- Unit tests for each service (OpenAI, GCS, context analysis, styles)
- Integration tests for API endpoints
- Mock-based testing for external service dependencies

## Deployment Information

### Cloud Run Deployment
- **Service Name**: `stylize-mcp-server`
- **Region**: `us-central1`
- **Project**: `stylize-mcp-server` (GCP project ID: 997481449751)
- **URL**: https://stylize-mcp-server-997481449751.us-central1.run.app
- **Current Status**: Fully operational with web interface and credit system
- **Last Updated**: 2025-06-03 (Complete trial upgrade and credit purchase system)

### Monitoring and Logs
```bash
# View Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=stylize-mcp-server AND resource.labels.location=us-central1" --limit=20 --format="table(timestamp,severity,textPayload)"

# Get service details
gcloud run services describe stylize-mcp-server --region=us-central1
```

### ✅ System Status (Fully Operational)
- **✅ Firestore Integration**: Complete user management with trial sessions and credit tracking
- **✅ Trial System**: Anonymous users get 5 free images with seamless upgrade flow
- **✅ Web Interface**: Beautiful forms for trial upgrade and credit purchase
- **✅ Credit System**: Complete credit purchase flow with 4 pricing tiers
- **✅ Image Generation**: Both single-style and multi-style generation working
- **✅ Authentication**: JWT-based user auth and API key management
- **✅ GCS Integration**: All generated images publicly accessible via signed URLs

### Authentication Development Notes
- For development: Set `AUTH_DEV_BYPASS=true` and `DEV_API_KEY=test-key` to use a simple development key
- For production: Create API keys in Secret Manager and set `AUTH_ENABLED=true`
- Health endpoint (`/health`) remains public for monitoring
- All other endpoints require valid API keys with appropriate permissions

### Available Permissions
- `stylize`: Access to `/stylize_image` endpoint and MCP image generation tools
- `styles`: Access to `/styles` endpoint and MCP style management tools  
- `mcp`: Access to all MCP tools and resources
- `admin`: Full access to all endpoints and operations

### Linting and Code Quality
```bash
# Install development dependencies
pip install ruff black isort

# Format code with black
black app/ tests/

# Sort imports with isort
isort app/ tests/

# Lint with ruff (fast Python linter)
ruff check app/ tests/

# Auto-fix linting issues
ruff check --fix app/ tests/
```

## Development Best Practices
- Always activate the venv before installing libraries
- Run tests before committing: `pytest`
- Format code before committing: `black app/ tests/`
- Fix linting issues: `ruff check --fix app/ tests/`