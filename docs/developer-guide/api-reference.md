# API Reference

Comprehensive documentation for the Stylize MCP Server REST API.

## Authentication

The server supports multiple authentication methods:

### API Key Authentication (Recommended)
Include your API key in the Authorization header:
```bash
curl -H "Authorization: Bearer your-api-key-here" \
     -X POST https://stylize-mcp-server-997481449751.us-central1.run.app/stylize_image
```

### Trial Session (Anonymous)
Access 5 free images without registration:
```bash
# No authentication needed - server automatically creates trial session
curl -X POST https://stylize-mcp-server-997481449751.us-central1.run.app/stylize_image \
  -F "style_id=van_gogh" \
  -F "user_prompt=a beautiful landscape"
```

### JWT Authentication (Registered Users)
Include JWT token from login:
```bash
curl -H "Authorization: Bearer jwt-token-here" \
     -X GET https://stylize-mcp-server-997481449751.us-central1.run.app/user/profile
```

## Core Image Generation

### POST /stylize_image

Transform images with artistic styles or generate from text descriptions.

**Authentication:** API key, trial session, or JWT token

#### Single Style Generation
```bash
curl -H "Authorization: Bearer your-api-key" \
     -X POST /stylize_image \
     -F "style_id=van_gogh" \
     -F "user_prompt=a serene mountain landscape" \
     -F "image=@photo.jpg"  # Optional: upload image to stylize
```

#### Multi-Style Generation (4 Random Styles)
```bash
# Omit style_id to generate 4 different artistic styles
curl -H "Authorization: Bearer your-api-key" \
     -X POST /stylize_image \
     -F "user_prompt=a serene mountain landscape"
```

#### Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `style_id` | string | No | Style to apply. Omit for 4 random styles |
| `user_prompt` | string | Yes | Description of desired image |
| `image` | file | No | Image file to stylize (multipart upload) |
| `project_context` | object | No | Brand colors, mood, target audience |

#### Response - Single Style
```json
{
  "original_id": "req-123",
  "style": "van_gogh",
  "stylized_image_url": "https://storage.googleapis.com/...",
  "prompt_used": "a serene mountain landscape, in the style of Vincent van Gogh...",
  "trial_info": {
    "images_used": 1,
    "images_remaining": 4,
    "signup_message": "You have 4 free images remaining. Sign up for 100 free images per month!",
    "signup_url": "/auth/register"
  }
}
```

#### Response - Multiple Styles
```json
{
  "original_id": "req-124", 
  "multiple_styles": true,
  "images": [
    {
      "style_id": "van_gogh",
      "style_name": "Van Gogh",
      "stylized_image_url": "https://storage.googleapis.com/...",
      "prompt_used": "a serene mountain landscape, in the style of Vincent van Gogh..."
    },
    {
      "style_id": "pixel_art",
      "style_name": "Pixel Art", 
      "stylized_image_url": "https://storage.googleapis.com/...",
      "prompt_used": "a serene mountain landscape, as pixel art..."
    },
    {
      "style_id": "flat_ui_icon",
      "style_name": "Flat UI Icon",
      "stylized_image_url": "https://storage.googleapis.com/...",
      "prompt_used": "a serene mountain landscape, as a minimalist flat design..."
    },
    {
      "style_id": "neumorphic_button", 
      "style_name": "Neumorphic Button",
      "stylized_image_url": "https://storage.googleapis.com/...",
      "prompt_used": "a serene mountain landscape, as a neumorphic UI element..."
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
```

### GET /styles

List all available artistic styles.

**Authentication:** API key, trial session, or JWT token

#### Response
```json
[
  {
    "id": "van_gogh",
    "name": "Van Gogh",
    "description": "Bold, swirling brush strokes with vibrant colors inspired by Vincent van Gogh",
    "example_prompt": "in the style of Vincent van Gogh with bold brush strokes and vibrant colors"
  },
  {
    "id": "pixel_art", 
    "name": "Pixel Art",
    "description": "Retro 8-bit video game aesthetic with blocky, pixelated appearance",
    "example_prompt": "as pixel art with a retro 8-bit video game aesthetic"
  },
  {
    "id": "flat_ui_icon",
    "name": "Flat UI Icon", 
    "description": "Modern, minimalist flat design with clean lines and solid colors",
    "example_prompt": "as a minimalist flat design icon with clean lines and solid colors"
  },
  {
    "id": "neumorphic_button",
    "name": "Neumorphic Button",
    "description": "Soft UI design with subtle shadows and highlights creating depth",
    "example_prompt": "as a neumorphic UI element with soft shadows and subtle depth"
  },
  {
    "id": "abstract_geometric",
    "name": "Abstract Geometric",
    "description": "Geometric patterns and shapes with abstract artistic interpretation", 
    "example_prompt": "as abstract geometric art with patterns and angular shapes"
  }
]
```

## Trial System

### GET /trial/status

Check current trial session usage and limits.

**Authentication:** None required (uses session tracking)

#### Response
```json
{
  "session_id": "trial-abc123",
  "images_used": 3,
  "images_remaining": 2,
  "can_generate": true,
  "signup_message": "You have 2 free images remaining. Sign up for 100 free images per month!",
  "signup_url": "/auth/register",
  "upgrade_options": [
    {
      "type": "free_account",
      "title": "Free Account",
      "description": "100 images per month",
      "action_url": "/auth/register"
    },
    {
      "type": "credit_purchase",
      "title": "Credit Packages", 
      "description": "Unlimited usage with credits",
      "action_url": "/pricing/packages"
    }
  ]
}
```

### GET /pricing/packages

View available credit packages for purchase.

**Authentication:** None required

#### Response
```json
[
  {
    "id": "starter",
    "name": "Starter Pack",
    "credits": 50,
    "bonus_credits": 5,
    "total_credits": 55,
    "price": 9.99,
    "popular": false
  },
  {
    "id": "popular", 
    "name": "Popular Pack",
    "credits": 200,
    "bonus_credits": 25,
    "total_credits": 225,
    "price": 29.99,
    "popular": true
  },
  {
    "id": "pro",
    "name": "Pro Pack", 
    "credits": 500,
    "bonus_credits": 75,
    "total_credits": 575,
    "price": 59.99,
    "popular": false
  },
  {
    "id": "enterprise",
    "name": "Enterprise Pack",
    "credits": 1000, 
    "bonus_credits": 200,
    "total_credits": 1200,
    "price": 99.99,
    "popular": false
  }
]
```

### POST /trial/convert

Convert anonymous trial session to registered user account.

**Authentication:** None required (uses trial session)

#### Request Body
```json
{
  "session_id": "trial-abc123",
  "email": "user@example.com",
  "password": "securepass123",
  "first_name": "John",
  "last_name": "Doe",
  "company": "Example Corp"
}
```

#### Response
```json
{
  "message": "Trial converted successfully",
  "user_id": "user-xyz789",
  "jwt_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "credits_awarded": 100,
  "subscription": {
    "tier": "free",
    "monthly_limit": 100,
    "current_usage": 0
  }
}
```

## User Management

### POST /auth/register

Register new user account.

**Authentication:** None required

#### Request Body
```json
{
  "email": "user@example.com",
  "password": "securepass123", 
  "first_name": "John",
  "last_name": "Doe",
  "company": "Example Corp"
}
```

#### Response
```json
{
  "message": "User registered successfully",
  "user_id": "user-xyz789",
  "jwt_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "subscription": {
    "tier": "free",
    "monthly_limit": 100,
    "credits": 100
  }
}
```

### POST /auth/login

Authenticate user and receive JWT token.

**Authentication:** None required

#### Request Body
```json
{
  "email": "user@example.com",
  "password": "securepass123"
}
```

#### Response
```json
{
  "jwt_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": "user-xyz789",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "subscription": {
    "tier": "free",
    "monthly_limit": 100,
    "current_usage": 25
  }
}
```

### GET /user/profile

Get current user profile information.

**Authentication:** JWT token required

#### Response
```json
{
  "id": "user-xyz789",
  "email": "user@example.com", 
  "first_name": "John",
  "last_name": "Doe",
  "company": "Example Corp",
  "created_at": "2024-01-01T00:00:00Z",
  "subscription": {
    "tier": "free",
    "monthly_limit": 100,
    "current_usage": 25
  }
}
```

### GET /user/credits

Get user credit balance and usage information.

**Authentication:** JWT token required

#### Response
```json
{
  "credits": 150,
  "monthly_credits": 100,
  "purchased_credits": 50,
  "current_month_usage": 25,
  "monthly_limit": 100,
  "subscription_tier": "free",
  "next_reset_date": "2024-02-01T00:00:00Z"
}
```

### POST /user/purchase-credits

Purchase additional credits.

**Authentication:** JWT token required

#### Request Body
```json
{
  "package_id": "starter"
}
```

#### Response
```json
{
  "message": "Credits purchased successfully",
  "package": {
    "name": "Starter Pack",
    "credits": 50,
    "bonus_credits": 5,
    "total_credits": 55,
    "price": 9.99
  },
  "new_balance": {
    "total_credits": 205,
    "purchased_credits": 105
  },
  "transaction_id": "txn-abc123"
}
```

### GET /user/dashboard

Get complete user dashboard data.

**Authentication:** JWT token required

#### Response
```json
{
  "user": {
    "id": "user-xyz789",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "credits": {
    "total": 205,
    "monthly": 100,
    "purchased": 105,
    "current_month_usage": 25
  },
  "subscription": {
    "tier": "free",
    "monthly_limit": 100,
    "next_reset": "2024-02-01T00:00:00Z"
  },
  "usage_stats": {
    "total_images_generated": 125,
    "this_month": 25,
    "favorite_style": "van_gogh"
  },
  "credit_packages": [
    {
      "id": "starter",
      "name": "Starter Pack",
      "total_credits": 55,
      "price": 9.99,
      "popular": false
    }
  ]
}
```

## API Key Management

### POST /user/api-keys

Create API key for current user.

**Authentication:** JWT token required

#### Request Body
```json
{
  "name": "My Integration",
  "permissions": ["stylize", "styles"]
}
```

#### Response
```json
{
  "key_id": "key-abc123",
  "name": "My Integration",
  "api_key": "sk-1234567890abcdef...",
  "permissions": ["stylize", "styles"],
  "created_at": "2024-01-01T00:00:00Z",
  "warning": "Store this API key securely. It will not be shown again."
}
```

### GET /user/api-keys

List user's API keys.

**Authentication:** JWT token required

#### Response
```json
[
  {
    "key_id": "key-abc123",
    "name": "My Integration",
    "permissions": ["stylize", "styles"],
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z",
    "last_used": "2024-01-15T10:30:00Z"
  }
]
```

### DELETE /user/api-keys/{key_id}

Revoke user's API key.

**Authentication:** JWT token required

#### Response
```json
{
  "message": "API key revoked successfully",
  "key_id": "key-abc123"
}
```

## Web Interface Endpoints

### GET /web/demo

Interactive demo page with trial credits and MCP integration guide.

**Authentication:** None required

**Response:** HTML page with:
- Drag & drop image upload interface
- Text-to-image generation form  
- Real-time credit tracking (5 free images)
- Style selection including "Surprise Me" (4 random styles)
- Step-by-step Claude Desktop MCP setup instructions
- Mobile-friendly responsive design

### GET /web/upgrade

Trial upgrade form for converting anonymous users to registered accounts.

**Authentication:** None required (uses session tracking)

**Response:** HTML form with:
- Trial session progress indicator
- Account creation form (email, password, name)
- Benefits of upgrading (100 free images/month)
- Professional responsive design

### POST /web/trial/upgrade

Process trial conversion via web form.

**Authentication:** None required (uses trial session)

#### Form Data
- `email`: User email address
- `password`: Account password
- `first_name`: User first name
- `last_name`: User last name
- `company`: Company name (optional)

#### Response
**Success:** Redirect to `/web/dashboard` with success message
**Error:** Redirect back to `/web/upgrade` with error message

### GET /web/dashboard

User dashboard with credit balance and purchase options.

**Authentication:** Cookie-based session (automatic after login/registration)

**Response:** HTML dashboard with:
- Current credit balance and usage statistics
- Monthly subscription limits and usage
- Credit purchase buttons for all 4 pricing tiers
- Recent image generation history
- Account management options
- Professional SaaS-quality interface

### POST /web/purchase

Process credit purchase via web form.

**Authentication:** Cookie-based session required

#### Form Data
- `package_id`: Credit package to purchase (`starter`, `popular`, `pro`, `enterprise`)

#### Response
**Success:** Redirect to `/web/dashboard` with purchase confirmation
**Error:** Redirect back to `/web/dashboard` with error message

### GET /web/logout

User logout endpoint.

**Authentication:** Cookie-based session

#### Response
Clears session cookies and redirects to homepage.

## Admin Endpoints

### POST /admin/api-keys

Create API key (admin only).

**Authentication:** API key with `admin` permission required

#### Request Body
```json
{
  "name": "Production Client",
  "permissions": ["stylize", "styles", "mcp"]
}
```

#### Response
```json
{
  "key_id": "key-abc123",
  "name": "Production Client",
  "api_key": "sk-1234567890abcdef...",
  "permissions": ["stylize", "styles", "mcp"],
  "created_at": "2024-01-01T00:00:00Z"
}
```

### GET /admin/api-keys

List all API keys.

**Authentication:** API key with `admin` permission required

#### Response
```json
[
  {
    "key_id": "key-abc123",
    "name": "Production Client",
    "permissions": ["stylize", "styles", "mcp"],
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z",
    "last_used": "2024-01-15T10:30:00Z"
  }
]
```

### PATCH /admin/api-keys/{key_id}

Update API key properties.

**Authentication:** API key with `admin` permission required

#### Request Body
```json
{
  "is_active": false,
  "permissions": ["stylize", "styles"]
}
```

#### Response
```json
{
  "message": "API key updated successfully",
  "key_id": "key-abc123",
  "is_active": false,
  "permissions": ["stylize", "styles"]
}
```

### DELETE /admin/api-keys/{key_id}

Deactivate API key.

**Authentication:** API key with `admin` permission required

#### Response
```json
{
  "message": "API key deactivated successfully",
  "key_id": "key-abc123"
}
```

## Security & Monitoring

### GET /admin/security/metrics

Get security metrics and abuse statistics.

**Authentication:** API key with `admin` permission required

#### Response
```json
{
  "daily_stats": {
    "total_requests": 1250,
    "trial_requests": 800, 
    "authenticated_requests": 450,
    "blocked_requests": 25,
    "high_risk_requests": 75
  },
  "abuse_prevention": {
    "captcha_challenges": 15,
    "vpn_detections": 45,
    "rate_limit_hits": 30,
    "device_fingerprints": 650
  },
  "trial_usage": {
    "active_sessions": 125,
    "exhausted_sessions": 200,
    "conversion_rate": 0.15
  },
  "top_risk_indicators": [
    {"type": "vpn_usage", "count": 45},
    {"type": "automation_detected", "count": 20},
    {"type": "suspicious_timing", "count": 15}
  ]
}
```

### POST /admin/security/report-abuse

Report manual abuse event.

**Authentication:** API key with `admin` permission required

#### Request Body
```json
{
  "session_id": "trial-abc123",
  "abuse_type": "manual_review", 
  "description": "Suspicious usage pattern detected",
  "action_taken": "session_blocked"
}
```

#### Response
```json
{
  "message": "Abuse event recorded successfully",
  "event_id": "abuse-xyz789",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### POST /security/challenge

Force CAPTCHA challenge for session.

**Authentication:** None required (public security endpoint)

#### Request Body
```json
{
  "session_id": "trial-abc123",
  "challenge_type": "recaptcha"
}
```

#### Response
```json
{
  "challenge_required": true,
  "challenge_type": "recaptcha",
  "site_key": "6LcXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  "challenge_url": "/security/verify-challenge"
}
```

### GET /static/js/fingerprint.js

Client-side device fingerprinting library.

**Authentication:** None required

**Response:** JavaScript library for device fingerprinting with:
- Canvas fingerprinting with spoofing detection
- WebGL context analysis  
- Screen resolution and font detection
- Mouse movement tracking
- Automated behavior detection

## Public Endpoints

### GET /health

Server health check.

**Authentication:** None required

#### Response
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "services": {
    "openai": "connected",
    "gcs": "connected", 
    "firestore": "connected",
    "redis": "connected"
  },
  "uptime": 86400
}
```

### GET /docs

OpenAPI documentation (Swagger UI).

**Authentication:** None required

Interactive API documentation with request/response examples.

## MCP Protocol

### /mcp/sse

Server-Sent Events transport for MCP clients.

**Authentication:** API key with `mcp` permission OR trial session

MCP tools available:
- `start_trial_session` - Begin anonymous trial
- `check_trial_status` - Monitor trial usage  
- `stylize_image` - Transform images with artistic styles
- `generate_image_from_text` - Create images from descriptions
- `list_styles` - Get available artistic styles
- `get_style_details` - Get detailed style information

### /mcp

JSON-RPC endpoint for MCP protocol.

**Authentication:** API key with `mcp` permission OR trial session

Same tools as SSE transport, accessible via JSON-RPC calls.

## Error Responses

### Standard Error Format
```json
{
  "error": {
    "code": "TRIAL_LIMIT_EXCEEDED",
    "message": "You have reached your trial limit of 5 images",
    "details": {
      "images_used": 5,
      "upgrade_options": [
        {
          "type": "free_account",
          "title": "Free Account", 
          "description": "100 images per month",
          "action_url": "/auth/register"
        }
      ]
    }
  }
}
```

### Common Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `TRIAL_LIMIT_EXCEEDED` | Trial image limit reached | 429 |
| `CONTENT_VIOLATION` | Image violates content policy | 400 |
| `INVALID_STYLE` | Style ID not found | 400 |
| `AUTHENTICATION_REQUIRED` | Valid API key or session required | 401 |
| `INSUFFICIENT_PERMISSIONS` | API key lacks required permissions | 403 |
| `RATE_LIMIT_EXCEEDED` | Too many requests | 429 |
| `SERVICE_UNAVAILABLE` | External service error | 503 |
| `INVALID_REQUEST` | Malformed request data | 400 |

## Rate Limits

| Endpoint | Authentication | Limit |
|----------|----------------|-------|
| `/stylize_image` | Trial Session | 5 images total |
| `/stylize_image` | API Key | Based on subscription |
| `/stylize_image` | Anonymous | 5 images per IP per day |
| `/auth/*` | None | 10 requests per minute |
| `/trial/status` | None | 60 requests per minute |
| All endpoints | API Key | 1000 requests per hour |

## Available Permissions

| Permission | Grants Access To |
|------------|------------------|
| `stylize` | `/stylize_image` endpoint and MCP image generation tools |
| `styles` | `/styles` endpoint and MCP style management tools |
| `mcp` | All MCP tools and resources |
| `admin` | All admin endpoints and operations |

## Best Practices

### For API Clients
1. **Always handle trial limits gracefully** - Guide users to upgrade when limits are reached
2. **Cache style information** - `/styles` endpoint results don't change frequently  
3. **Use multi-style generation for exploration** - Omit `style_id` to show variety
4. **Implement retry logic** - Handle temporary service unavailability
5. **Validate images before upload** - Check file size and format client-side

### For MCP Integration
1. **Start with trial sessions** - Let users explore before requiring signup
2. **Progressive enhancement** - Show more features as users engage
3. **Natural error handling** - Convert technical errors to helpful guidance
4. **Context awareness** - Use project context for brand-aligned results
5. **Performance optimization** - Cache sessions and styles for better UX

### Security Considerations
1. **Store API keys securely** - Never expose in client-side code
2. **Use HTTPS** - All communication must be encrypted
3. **Implement request signing** - For additional security in sensitive applications
4. **Monitor usage patterns** - Track for unusual activity
5. **Rotate API keys regularly** - Best practice for production systems