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

### 🛡️ Trial Abuse Prevention System

The server includes a comprehensive **multi-layered security system** to prevent abuse of the freemium trial while maintaining zero friction for legitimate users.

#### Security Configuration
```bash
# Security System
SECURITY_ENABLED=true                    # Enable comprehensive abuse prevention (default: false)
HIGH_RISK_THRESHOLD=0.7                 # Risk score threshold for challenges (default: 0.7)
FINGERPRINTING_ENABLED=true            # Enable device fingerprinting (default: true)

# VPN & Proxy Detection
VPN_DETECTION_PAID_APIS=true           # Enable premium VPN detection APIs (default: false)
VPN_DETECTION_TIMEOUT=5                # VPN API timeout in seconds (default: 5)
VPN_CACHE_DURATION=3600                # VPN result cache duration in seconds (default: 3600)
IPQUALITYSCORE_API_KEY=your_key        # IPQualityScore API key (optional)
PROXYCHECK_API_KEY=your_key            # ProxyCheck.io API key (optional)
GEOIP_DATABASE_PATH=/path/to/GeoLite2  # GeoIP database path (optional)

# Rate Limiting
TRIAL_CREATION_PER_IP=5                # Max trial sessions per IP per day (default: 5)
TRIAL_CREATION_PER_DEVICE=3            # Max trial sessions per device per day (default: 3)
IMAGE_GENERATION_PER_SESSION=5         # Max images per trial session (default: 5)
GLOBAL_DAILY_LIMIT=10000               # Global daily image generation limit (default: 10000)
RATE_LIMIT_WINDOW_HOURS=24             # Rate limit window in hours (default: 24)

# CAPTCHA Integration
RECAPTCHA_SITE_KEY=your_site_key       # Google reCAPTCHA site key (optional)
RECAPTCHA_SECRET_KEY=your_secret       # Google reCAPTCHA secret key (optional)
HCAPTCHA_SITE_KEY=your_site_key        # hCAPTCHA site key (optional)
HCAPTCHA_SECRET_KEY=your_secret        # hCAPTCHA secret key (optional)

# Monitoring & Logging
ABUSE_LOG_LEVEL=INFO                   # Abuse event logging level (default: INFO)
SECURITY_METRICS_ENABLED=true         # Enable security metrics collection (default: true)
```

#### Protection Services

The system includes several specialized protection services:

**Device Fingerprinting Service** (`app/fingerprint_service.py`)
- Client-side JavaScript fingerprinting with spoofing detection
- Server-side request analysis and header fingerprinting
- Cross-session device tracking with privacy-conscious hashing

**VPN Detection Service** (`app/vpn_detection_service.py`)
- Multi-API VPN/proxy detection with intelligent fallbacks
- Known VPN range checking and datacenter hosting detection
- Risk scoring based on IP reputation and geolocation analysis

**Behavioral Analysis Service** (`app/behavior_analysis_service.py`)
- Automation detection using timing patterns and request sequences
- Mouse movement tracking and user interaction analysis
- Progressive challenge escalation based on behavior patterns

**Risk Scoring Service** (`app/risk_scoring_service.py`)
- ML-based risk assessment combining multiple signals
- Dynamic threshold adjustment based on threat patterns
- Confidence scoring to minimize false positives

**Rate Limiting Service** (`app/rate_limiting_service.py`)
- Multi-dimensional rate limiting (IP, device, session, global)
- Sliding window algorithms with burst protection
- Risk-based limit adjustment for verified users

**Abuse Monitoring Service** (`app/abuse_monitoring_service.py`)
- Real-time abuse event logging and pattern detection
- Automated response triggers and admin alerting
- Security metrics dashboard and reporting

#### Graceful Degradation

The security system is designed for **zero-friction operation**:

- **Backward compatible**: Works without any configuration changes
- **Progressive enhancement**: Additional layers activate as services are configured
- **Intelligent fallbacks**: Degrades gracefully when external APIs are unavailable
- **Development friendly**: Can be completely disabled for local development

#### Security Testing
```bash
# Test protection services individually
python -m pytest tests/test_abuse_prevention.py -v

# Test with security enabled
SECURITY_ENABLED=true pytest tests/test_trial_service.py

# Verify fingerprinting service
curl http://localhost:8000/static/js/fingerprint.js

# Check rate limiting behavior
curl -X POST http://localhost:8000/trial/status -v
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

### ✅ System Status (Fully Operational + Enhanced Security)
- **✅ Firestore Integration**: Complete user management with trial sessions and credit tracking
- **✅ Trial System**: Anonymous users get 5 free images with seamless upgrade flow
- **✅ Advanced Security**: Multi-layered abuse prevention with device fingerprinting, VPN detection, and behavioral analysis
- **✅ Web Interface**: Beautiful forms for trial upgrade and credit purchase
- **✅ Credit System**: Complete credit purchase flow with 4 pricing tiers
- **✅ Image Generation**: Both single-style and multi-style generation working
- **✅ Authentication**: JWT-based user auth and API key management
- **✅ Rate Limiting**: Sophisticated multi-dimensional rate limiting with risk-based adjustment
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

## AI Assistant Integration via MCP

### Overview
This server is designed to be used by AI assistants (like Claude) through the Model Context Protocol (MCP). AI assistants connect to the `/mcp` endpoint and use the available tools to help users create and stylize images through natural conversation.

### Natural Conversation Flow Examples

#### **Scenario 1: First-Time User - Image Stylization**
```
User: "Can you make this photo look like a Van Gogh painting?"

AI Assistant Internal Flow:
1. start_trial_session() → Gets session_id for anonymous user
2. User uploads photo to chat
3. stylize_image(image_base64="...", style_id="van_gogh", session_id="trial-123")
4. Present result to user with remaining trial info

AI Assistant Response:
"I've transformed your photo into Van Gogh's distinctive style with bold, swirling brush strokes and vibrant colors! Here's your artistic interpretation. You have 4 more free transformations remaining in your trial."
```

#### **Scenario 2: Style Exploration**
```
User: "What different art styles can you create?"

AI Assistant Internal Flow:
1. list_styles() → Get all available styles
2. get_style_details() for each style → Get descriptions

AI Assistant Response:
"I can create images in 5 different artistic styles:
• Van Gogh: Bold, swirling brush strokes with vibrant colors
• Pixel Art: Retro 8-bit aesthetic with blocky pixels
• Flat UI Icon: Modern minimalist design with solid colors
• Neumorphic Button: Soft, dimensional interface elements
• Glassmorphic Card: Frosted glass transparency effects

Would you like me to show your image in multiple styles, or do you have a preference?"
```

#### **Scenario 3: Multi-Style Generation**
```
User: "Show me this landscape in different artistic styles"

AI Assistant Internal Flow:
1. stylize_image(image_base64="...", session_id="trial-123") 
   # Note: Omitting style_id automatically generates 4 random styles
2. Present all 4 variations

AI Assistant Response:
"Here are 4 different artistic interpretations of your landscape:

1. **Van Gogh Style**: Swirling sky with expressive brush strokes
2. **Pixel Art**: Retro gaming aesthetic with blocky trees
3. **Flat UI**: Clean, minimal landscape icon
4. **Glassmorphic**: Transparent, modern glass effect

Which style resonates with you? I can create more variations in that style!"
```

#### **Scenario 4: Text-to-Image Creation**
```
User: "Create a logo for my coffee shop called 'Morning Brew'"

AI Assistant Internal Flow:
1. Check trial status with check_trial_status()
2. generate_image_from_text(prompt="coffee shop logo for Morning Brew, warm and inviting", style_id="flat_ui_icon")

AI Assistant Response:
"I've created a modern flat UI logo for Morning Brew with warm, inviting coffee elements. The clean design would work well across different media. Would you like me to try other styles or refine this design further?"
```

#### **Scenario 5: Brand-Aware Generation**
```
User: "I need marketing images for my tech startup. Our brand colors are blue and orange, and we want a modern, professional look."

AI Assistant Internal Flow:
1. generate_image_from_text(
     prompt="tech startup marketing image with innovative technology",
     style_id="flat_ui_icon",
     project_context={
       "brand_colors": ["#007ACC", "#FF6B35"], 
       "mood": "professional and modern",
       "target_audience": "tech professionals"
     }
   )

AI Assistant Response:
"I've created marketing imagery that incorporates your blue and orange brand colors with a modern, professional aesthetic perfect for tech audiences. The flat design style ensures it will work well across digital platforms."
```

### Progressive User Journey Management

#### **Phase 1: Trial Discovery (Images 1-3)**
```python
# AI assistant focuses on demonstrating value without mentioning limits
if trial_info.images_used <= 3:
    # Just show the result enthusiastically
    response = f"Here's your {style_applied} styled image! The {describe_style_effect()} really brings out the artistic character."
```

#### **Phase 2: Trial Awareness (Images 4-5)**
```python
# AI assistant mentions remaining trial images casually
if trial_info.images_remaining <= 2:
    response = f"Here's your stylized image! You have {trial_info.images_remaining} trial images remaining. After that, you can sign up for 100 free images per month."
```

#### **Phase 3: Conversion Opportunity (Trial Exhausted)**
```python
# AI assistant provides clear upgrade path
if trial_info.images_remaining == 0:
    response = "You've used all 5 trial images! I can help you sign up for a free account with 100 images per month, or you can purchase credits for unlimited usage. Would you like me to guide you through the signup process?"
```

### Error Handling Patterns

#### **Trial Limit Exceeded**
```python
try:
    result = await stylize_image(session_id="trial-123", ...)
except TrialLimitExceeded:
    return """You've reached your trial limit, but don't worry! You have great options:
    
    🆓 **Free Account**: Sign up for 100 free images per month
    💳 **Credit Packages**: Purchase credits for unlimited usage
    
    I can help you sign up or show you the pricing options. What would you prefer?"""
```

#### **Content Policy Violation**
```python
try:
    result = await stylize_image(image_base64="...", ...)
except ContentViolation:
    return "I can't process this image due to content guidelines. Please try a different image, and I'll be happy to help with the stylization!"
```

#### **Service Temporarily Unavailable**
```python
try:
    result = await generate_image_from_text(...)
except ServiceUnavailable:
    return "The image generation service is temporarily unavailable. Please try again in a few minutes, or I can help you with other tasks in the meantime."
```

### Tool Orchestration Patterns

#### **Discover → Generate → Refine Workflow**
```python
# 1. Style Discovery Phase
styles = await list_styles()
# Present options to user conversationally

# 2. Initial Generation
if user_wants_multiple_styles:
    result = await stylize_image(..., session_id="trial-123")  # Omit style_id for 4 random
else:
    result = await stylize_image(..., style_id=user_selected_style, session_id="trial-123")

# 3. Refinement Phase
if user_wants_variations:
    refined_result = await generate_image_from_text(
        prompt=f"refined version of {user_feedback}",
        style_id=preferred_style
    )
```

#### **Context-Aware Multi-Modal Workflow**
```python
# When user provides reference image + text description
context_summary = analyze_uploaded_image(reference_image)

# Generate with both visual and textual context
result = await stylize_image(
    image_base64=user_uploaded_image,
    style_id="van_gogh",
    user_prompt="make it more vibrant and energetic",
    project_context={
        "reference_style": context_summary,
        "mood": "energetic and vibrant"
    }
)
```

### Authentication Flow Management

#### **Seamless Trial-to-API Key Transition**
```python
class MCPImageClient:
    def __init__(self):
        self.session_id = None
        self.api_key = None
    
    async def ensure_auth(self):
        """Ensure we have valid authentication for image generation."""
        if not self.api_key and not self.session_id:
            # Start trial session for new users
            trial = await start_trial_session()
            self.session_id = trial["session_id"]
            return f"Started your free trial! You have {trial['images_remaining']} images to explore."
    
    async def generate_image(self, **kwargs):
        """Generate image with automatic auth handling."""
        auth_message = await self.ensure_auth()
        
        try:
            if self.api_key:
                return await stylize_image(api_key=self.api_key, **kwargs)
            else:
                return await stylize_image(session_id=self.session_id, **kwargs)
        except TrialExhausted:
            return {
                "error": "trial_exhausted",
                "message": "Your trial has ended! Would you like to sign up for 100 free images per month?",
                "upgrade_options": await self.get_upgrade_options()
            }
    
    async def handle_user_upgrade(self, user_choice):
        """Handle user decision to upgrade."""
        if user_choice == "signup":
            return "Great! Visit this link to create your free account: /web/upgrade"
        elif user_choice == "credits":
            packages = await self.get_credit_packages()
            return f"Here are the available credit packages: {format_packages(packages)}"
```

### Best Practices for AI Assistants

#### **Value-First Approach**
- Always demonstrate capabilities before mentioning limitations
- Focus on the creative result, not the technical process
- Use trial limits as gentle guidance, not barriers

#### **Natural Language Integration**
- Embed tool calls seamlessly in conversation flow
- Translate technical responses into conversational language
- Provide context and suggestions for next steps

#### **Progressive Disclosure**
- Start with simple single-style generation
- Introduce multi-style options based on user interest
- Offer advanced features (project context) for engaged users

#### **Graceful Limit Handling**
- Never abruptly stop service when limits are reached
- Always provide clear next steps and options
- Make upgrading feel like a natural progression, not a paywall

## Development Best Practices
- Always activate the venv before installing libraries
- Run tests before committing: `pytest`
- Format code before committing: `black app/ tests/`
- Fix linting issues: `ruff check --fix app/ tests/`