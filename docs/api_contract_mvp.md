# Stylize MCP Server - MVP API Contract

This document outlines the API contract for the Minimum Viable Product (MVP) version of the Stylize MCP Server.

## Endpoints

### 1. Stylize Image

**Endpoint:** `POST /stylize_image`

**Purpose:** Transform a user-uploaded image according to a specified style.

**Request Format:**
```
Content-Type: multipart/form-data
```

**Request Parameters:**
- `image` (file, required): The image file to be stylized. Supported formats: JPEG, PNG.
- `style_id` (string, required): The identifier of the style to apply. Must be a valid style ID from the style catalog.

**Response (Success - 200 OK):**
```json
{
  "original_id": "string",         // Unique identifier for the original image
  "style": "string",              // The style ID that was applied
  "stylized_image_url": "string"   // URL to access the stylized image
}
```

**Response (Error - 400 Bad Request):**
```json
{
  "error": "string"               // Error message describing the issue
}
```

**Possible Error Scenarios:**
- Invalid image format (not JPEG/PNG)
- Image size exceeds limits
- Invalid or unsupported style_id
- Image content violates safety policy (SafeSearch)

---

### 2. Get Available Styles

**Endpoint:** `GET /styles`

**Purpose:** Retrieve the list of available styles that can be applied to images.

**Request Format:** No request parameters.

**Response (Success - 200 OK):**
```json
[
  {
    "id": "string",               // Unique identifier for the style
    "name": "string",             // Human-readable name of the style
    "description": "string",      // Description of what the style looks like
    "prompt_fragment": "string"   // The text fragment used in prompts to achieve this style
  },
  ...
]
```

---

### 3. Health Check

**Endpoint:** `GET /health`

**Purpose:** Verify that the service is running and healthy.

**Request Format:** No request parameters.

**Response (Success - 200 OK):**
```json
{
  "status": "ok"
}
```

---

## Authentication & Rate Limiting

### MVP Authentication Decision

For the MVP, no specific authentication will be implemented for `/stylize_image` or `/styles`. Requests will be processed under a single global user context for quota purposes initially. User identification for quotas will be handled via client IP or a simple, non-validated header if necessary.

### Rate Limiting

The service will implement the following rate limits:
- Global daily cap: Limited number of API calls per day across all users (configurable)
- Per-user/IP daily quota: Limited number of API calls per user/IP per day (configurable)

When a quota is exceeded, the API will return a 429 Too Many Requests response with an appropriate error message.
