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
- `image` (file, required): The primary image file to be stylized (e.g., a sketch, a photo to transform). Required. Supported formats: JPEG, PNG.
- `style_id` (string, required): The identifier of the style to apply. Must be a valid style ID from the style catalog.
- `project_context` (string, optional): An optional JSON string containing structured contextual information about the project. This context will be analyzed by the server to refine the image generation prompt. If invalid JSON is provided, an error will be returned.

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
- Invalid `project_context` JSON format
- Invalid `reference_logo_image_base64` format (if not valid Base64)

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

## MCP Tools

### 1. stylize_image_mcp_tool

**Tool Name:** `stylize_image_mcp_tool`

**Purpose:** Transform an image according to a specified style via MCP.

**MCP Request Parameters (within the `arguments` object of an MCP call):**
- `primary_image_base64` (string, required): The raw primary image file content (e.g., a sketch, a photo for general stylization), Base64 encoded.
- `style_id` (string, required): The identifier of the style to apply. Must be a valid style ID from the style catalog.
- `user_prompt` (string, optional): Additional descriptive text to guide the image stylization.
- `project_context` (object, optional): A JSON object providing project context, including an optional `reference_logo_image_base64` for logo refreshes. See schema defined under the HTTP `POST /stylize_image` endpoint.

**MCP Response (Success):**
- Return Type: `string`
- Description: A URL to access the successfully stylized image.

**Example Conceptual MCP Request Payload (for illustration):**
```json
// Conceptual example of how an MCP client might structure the call
{
  "mcp_version": "1.0", // Or relevant MCP version
  "tool_name": "stylize_image_mcp_tool",
  "tool_id": "unique_call_id", // Or relevant MCP call ID
  "arguments": {
    "primary_image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=", // Placeholder Base64 data
    "style_id": "van_gogh",
    "user_prompt": "A beautiful landscape", // Optional
    "project_context": { // Optional
      "project_name": "Mountain Resort Rebrand",
      "project_description": "Luxury mountain resort logo refresh",
      "brand_colors": ["#003366", "#FFFFFF", "#7CAD3A"],
      "artistic_mood": "elegant",
      "reference_logo_image_base64": "iVBORw0KGgoAAAAN..." // Base64 encoded existing logo image
    }
  }
}
```

**MCP Response (Error):**
If an error occurs, the MCP tool will return an error string describing the issue, such as "Invalid style ID", "Image content not allowed by safety policy", or "Invalid project_context JSON format".

---

## ProjectContext Object Schema

```json
// ProjectContext Object Schema
{
  "project_name": "string (optional)",
  "project_description": "string (optional) - A brief description of the project or the subject of the image.",
  "target_audience": "string (optional) - Intended audience for the design.",
  "keywords": ["string (optional) - List of relevant keywords, concepts, or themes."],
  "brand_colors": ["hex_code (optional) - Up to 3 primary brand colors (e.g., '#FF0000')."],
  "desired_elements": ["string (optional) - Specific elements or objects that should be included."],
  "avoid_elements": ["string (optional) - Specific elements or objects to avoid."],
  "artistic_mood": "string (optional) - e.g., 'playful', 'serious', 'futuristic', 'minimalist'.",
  "reference_logo_image_base64": "string (optional) - Base64 encoded string of an existing logo image. If provided, the generation will aim to refresh or create variations based on this reference."
}
```

The server will perform a basic analysis on these fields to construct a more targeted prompt.

---

## Authentication & Rate Limiting

### MVP Authentication Decision

For the MVP, no specific authentication will be implemented for `/stylize_image` or `/styles`. Requests will be processed under a single global user context for quota purposes initially. User identification for quotas will be handled via client IP or a simple, non-validated header if necessary.

### Rate Limiting

The service will implement the following rate limits:
- Global daily cap: Limited number of API calls per day across all users (configurable)
- Per-user/IP daily quota: Limited number of API calls per user/IP per day (configurable)

When a quota is exceeded, the API will return a 429 Too Many Requests response with an appropriate error message.
