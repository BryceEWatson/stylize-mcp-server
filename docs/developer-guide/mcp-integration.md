# MCP Integration Guide

Comprehensive guide for integrating the Stylize MCP Server with AI assistants through the Model Context Protocol (MCP).

## Overview

The Stylize MCP Server is specifically designed to enhance AI assistants with professional-grade image generation and stylization capabilities. Rather than requiring users to learn technical APIs, AI assistants can seamlessly integrate these capabilities into natural conversations.

## Quick Start Integration

### Configure Claude Desktop

1. **Download Claude Desktop**: Get it from [claude.ai/download](https://claude.ai/download)

2. **Add MCP Configuration**:
   - **Windows:** Open `%APPDATA%\Claude\claude_desktop_config.json`
   - **macOS:** Open `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Add this configuration:**

```json
{
  "mcpServers": {
    "stylize-server": {
      "transport": {
        "type": "sse",
        "url": "https://stylize-mcp-server-997481449751.us-central1.run.app/mcp/sse"
      }
    }
  }
}
```

3. **Restart Claude Desktop**

### Alternative MCP Clients

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

## Authentication Modes

### Trial Mode (Recommended for New Users)
Perfect for letting users explore capabilities without signup:

```python
# Start trial session
trial = await client.call_tool("start_trial_session", {})
session_id = trial["session_id"]

# Use trial session for image generation
result = await client.call_tool("stylize_image", {
    "image_base64": "...",
    "style_id": "van_gogh", 
    "session_id": session_id
})
```

### API Key Mode (For Production AI Assistants)
For authenticated access with higher limits:

```python
# Full access with API key
result = await client.call_tool("stylize_image", {
    "image_base64": "...",
    "style_id": "van_gogh",
    "api_key": "your-production-key"
})
```

## Available MCP Tools

### 🚀 Trial Session Management

#### `start_trial_session`
Begin anonymous trial with 5 free images.

**Parameters:** None

**Returns:**
```json
{
  "session_id": "trial-abc123",
  "images_remaining": 5,
  "upgrade_options": [
    {
      "type": "free_account",
      "title": "Free Account",
      "description": "100 images per month",
      "action_url": "/auth/register"
    }
  ]
}
```

**AI Assistant Usage:**
```
"Let me start a free trial for you to explore image generation"
```

#### `check_trial_status`
Monitor trial usage and guide users toward upgrades.

**Parameters:**
- `session_id` (string): Trial session ID

**Returns:**
```json
{
  "session_id": "trial-abc123",
  "images_used": 3,
  "images_remaining": 2,
  "can_generate": true,
  "signup_message": "You have 2 free images remaining. Sign up for 100 free images per month!",
  "upgrade_options": [...]
}
```

**AI Assistant Usage:**
```
"You have 2 trial images remaining" with upgrade suggestions
```

### 🎨 Intelligent Image Generation

#### `stylize_image`
Transform uploaded images with artistic styles.

**Parameters:**
- `image_base64` (string): Base64-encoded image data
- `style_id` (string, optional): Specific style to apply. **Omit for 4 random styles!**
- `user_prompt` (string, optional): Additional description
- `project_context` (object, optional): Brand colors, mood, target audience
- `session_id` (string, optional): Trial session ID
- `api_key` (string, optional): API key for authenticated access

**Single Style Response:**
```json
{
  "stylized_image_url": "https://storage.googleapis.com/...",
  "style_applied": "van_gogh",
  "prompt_used": "a beautiful sunset, in the style of Vincent van Gogh...",
  "trial_info": {
    "images_used": 1,
    "images_remaining": 4
  }
}
```

**Multi-Style Response (when style_id omitted):**
```json
{
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
    "images_remaining": 0
  }
}
```

**AI Assistant Usage:**
- **Single Style**: "I'll apply Van Gogh's style to your photo"
- **Multi-Style**: "Let me show you 4 different artistic interpretations"

#### `generate_image_from_text`
Create images from text descriptions.

**Parameters:**
- `prompt` (string): Description of desired image
- `style_id` (string, optional): Specific style to apply. **Omit for 4 random styles!**
- `project_context` (object, optional): Brand guidelines
- `session_id` (string, optional): Trial session ID
- `api_key` (string, optional): API key for authenticated access

**Returns:** Same format as `stylize_image`

**AI Assistant Usage:**
- **Guided Creation**: "I'll create a logo based on your description"
- **Style Variety**: "Let me generate this in multiple styles for you to choose"

### 🎯 Style Discovery & Guidance

#### `list_styles`
Discover available artistic styles.

**Parameters:**
- `api_key` (string, optional): API key for authenticated access

**Returns:**
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
  }
]
```

**AI Assistant Usage:**
```
"Here are the artistic styles I can create for you..."
```

#### `get_style_details`
Get detailed information about a specific style.

**Parameters:**
- `style_id` (string): Style identifier
- `api_key` (string, optional): API key for authenticated access

**Returns:**
```json
{
  "id": "van_gogh",
  "name": "Van Gogh",
  "description": "Bold, swirling brush strokes with vibrant colors inspired by Vincent van Gogh",
  "example_prompt": "in the style of Vincent van Gogh with bold brush strokes and vibrant colors",
  "best_for": ["artistic expression", "emotional impact", "creative projects"],
  "example_use_cases": ["art projects", "creative websites", "expressive branding"]
}
```

**AI Assistant Usage:**
```
"Van Gogh style uses bold, swirling brush strokes that..."
```

## Natural Conversation Patterns

### Pattern 1: Discovery-Driven Exploration

Help users discover capabilities through natural conversation:

```python
class ImageStyleDiscovery:
    async def handle_style_inquiry(self, user_message: str):
        """Handle questions like 'What can you do with images?'"""
        
        # Get available styles
        styles = await client.call_tool("list_styles", {"api_key": self.api_key})
        
        # Create conversational response
        style_descriptions = []
        for style in styles:
            details = await client.call_tool("get_style_details", {
                "style_id": style["id"],
                "api_key": self.api_key
            })
            style_descriptions.append(f"• **{style['name']}**: {style['description']}")
        
        return f"""I can transform images in {len(styles)} different artistic styles:

{chr(10).join(style_descriptions)}

Would you like to try one of these styles, or shall I show you examples with your own image?"""

    async def handle_style_demonstration(self, user_image, user_preference=None):
        """Show multiple styles or focus on user preference."""
        
        if user_preference:
            # Single style based on preference
            result = await client.call_tool("stylize_image", {
                "image_base64": user_image,
                "style_id": user_preference,
                "session_id": self.session_id
            })
            return f"Here's your image in {result['style_applied']} style! {self.describe_result(result)}"
        else:
            # Multiple styles for exploration
            result = await client.call_tool("stylize_image", {
                "image_base64": user_image,
                # Omitting style_id generates 4 random styles
                "session_id": self.session_id
            })
            
            descriptions = []
            for img in result["images"]:
                descriptions.append(f"**{img['style_name']}**: {self.describe_style_effect(img)}")
            
            return f"""Here are 4 different artistic interpretations of your image:

{chr(10).join(descriptions)}

Which style appeals to you most? I can create more variations in that style!"""
```

### Pattern 2: Progressive Enhancement

Guide users from basic to advanced features naturally:

```python
class ProgressiveImageGeneration:
    def __init__(self):
        self.user_skill_level = "beginner"  # beginner, intermediate, advanced
        self.session_history = []
    
    async def generate_with_context(self, user_request: str, user_image=None):
        """Adapt response complexity based on user experience."""
        
        if self.user_skill_level == "beginner":
            # Simple, single-style generation
            return await self._simple_generation(user_request, user_image)
        
        elif self.user_skill_level == "intermediate":
            # Offer multi-style options
            return await self._multi_style_generation(user_request, user_image)
        
        else:  # advanced
            # Include project context and brand awareness
            return await self._advanced_generation(user_request, user_image)
    
    async def _simple_generation(self, request: str, image=None):
        """Focus on single, clear result."""
        style = self._detect_style_preference(request) or "van_gogh"
        
        if image:
            result = await client.call_tool("stylize_image", {
                "image_base64": image,
                "style_id": style,
                "session_id": self.session_id
            })
        else:
            result = await client.call_tool("generate_image_from_text", {
                "prompt": request,
                "style_id": style,
                "api_key": self.api_key
            })
        
        # Simple, enthusiastic response
        return f"Here's your {style.replace('_', ' ').title()} style image! The {self._describe_style_effect(style)} really brings your vision to life."
    
    async def _advanced_generation(self, request: str, image=None, brand_context=None):
        """Include project context and brand considerations."""
        
        # Extract brand context from conversation history or request
        project_context = self._extract_project_context(request, brand_context)
        
        if image:
            result = await client.call_tool("stylize_image", {
                "image_base64": image,
                "style_id": self._smart_style_selection(request, project_context),
                "user_prompt": self._refine_prompt(request),
                "project_context": project_context,
                "session_id": self.session_id
            })
        else:
            result = await client.call_tool("generate_image_from_text", {
                "prompt": self._enhance_prompt_with_context(request, project_context),
                "style_id": self._smart_style_selection(request, project_context),
                "project_context": project_context,
                "api_key": self.api_key
            })
        
        return f"""I've created a brand-aligned image that considers your {project_context.get('target_audience', 'audience')} and incorporates your brand elements. 

{self._describe_brand_integration(result, project_context)}

Would you like me to adjust the brand integration or try alternative approaches?"""
```

### Pattern 3: Error Recovery and Conversion

Handle limits and errors gracefully while guiding users toward value:

```python
class ErrorRecoveryHandler:
    async def handle_trial_limit(self, user_request: str):
        """Convert trial limitation into upgrade opportunity."""
        
        # Check current trial status
        status = await client.call_tool("check_trial_status", {
            "session_id": self.session_id
        })
        
        if not status["can_generate"]:
            upgrade_options = status.get("upgrade_options", [])
            
            return f"""You've explored the full trial experience with 5 image generations! 

Based on your usage, here are your best options:

🆓 **Free Account** (Recommended): 100 images per month
   Perfect for regular creative projects

💳 **Credit Packages**: Unlimited usage
   {self._format_credit_packages(upgrade_options)}

I can help you sign up for the free account right now, or you can purchase credits for immediate unlimited access. What works best for you?"""
    
    async def handle_content_violation(self, user_image, user_request):
        """Guide users through content policy issues."""
        
        return """I can't process this particular image due to content guidelines, but I'd love to help you create something amazing! 

Here are some alternatives:
• Try a different image that shows [specific suggestions based on violation type]
• I can generate a new image from your description instead
• Let me suggest some creative directions that would work well

What would you like to try?"""
    
    async def handle_service_unavailable(self, user_request):
        """Provide helpful alternatives during downtime."""
        
        return """The image generation service is temporarily busy, but I can help in other ways:

• **Style Planning**: Let's discuss what style would work best for your project
• **Prompt Refinement**: I can help you craft the perfect description for when service returns
• **Creative Consultation**: We can explore color schemes, composition ideas, and artistic direction

What aspect of your creative project would you like to explore while we wait?"""
```

## Natural Conversation Examples

### Beginner User Experience
```
👤 User: "Can you help me make my photo look artistic?"

🤖 Claude: "I'd love to help! Let me start a free trial for you and create some artistic versions of your photo. Please upload your image and I'll show you several different styles."

[User uploads a landscape photo]

🤖 Claude: "I've created 4 different artistic interpretations of your landscape:

🎨 Van Gogh Style: Bold, swirling brush strokes with vibrant colors
🎮 Pixel Art: Nostalgic 8-bit retro gaming aesthetic  
💻 Flat UI: Clean, modern minimalist design
✨ Neumorphic: Soft, tactile interface with subtle shadows

Which style resonates with you? You have 1 more trial image remaining, or I can help you sign up for 100 free images per month!"
```

### Creative Project Examples
```
👤 User: "I need a logo for my coffee shop called 'Morning Brew'"

🤖 Claude: "Perfect! I'll create several logo concepts for Morning Brew. Let me generate some options in different styles to give you variety."

[Claude generates 4 different logo styles]

🤖 Claude: "Here are 4 different logo approaches for Morning Brew:

☕ Van Gogh Style: Artistic, swirling design with warm coffee tones
🎯 Flat UI Style: Clean, modern logo perfect for signage and apps  
🎪 Pixel Art Style: Retro charm that could work great for a nostalgic brand
🌟 Neumorphic Style: Soft, dimensional design for premium feel

Which direction appeals to you? I can refine any of these or create variations!"
```

### Brand-Aware Generation
```
👤 User: "I'm creating marketing materials for my tech startup. Our brand colors are blue and orange, and we want a modern, professional look."

🤖 Claude: "Excellent! I'll create marketing imagery that incorporates your blue and orange brand colors with a modern, professional aesthetic. Let me generate some concepts that would work well for tech audiences."

[Claude uses project context to generate brand-aware images]

🤖 Claude: "I've created several marketing concepts that incorporate your brand identity:

🎯 **Flat UI Style**: Clean, professional designs perfect for your tech brand
🔷 **Glassmorphic Style**: Modern, cutting-edge look that appeals to tech audiences

Each design integrates your blue and orange color palette while maintaining that professional, modern feel you're looking for. These would work well across digital platforms, presentations, and marketing materials.

Would you like me to create variations of any particular style, or explore different concepts?"
```

## Advanced Integration Patterns

### Multi-Modal Context Understanding

```python
class ContextAwareGeneration:
    async def process_multi_modal_request(self, text_request: str, reference_images: list = None, brand_guidelines: dict = None):
        """Handle complex requests with multiple context sources."""
        
        # Build comprehensive context
        project_context = {}
        
        # Extract context from reference images
        if reference_images:
            context_analysis = await self._analyze_reference_images(reference_images)
            project_context.update(context_analysis)
        
        # Incorporate brand guidelines
        if brand_guidelines:
            project_context.update({
                "brand_colors": brand_guidelines.get("colors", []),
                "mood": brand_guidelines.get("tone", ""),
                "target_audience": brand_guidelines.get("audience", "")
            })
        
        # Extract intent and style preference from text
        intent_analysis = self._analyze_user_intent(text_request)
        optimal_style = self._select_optimal_style(intent_analysis, project_context)
        
        # Generate with full context
        result = await client.call_tool("generate_image_from_text", {
            "prompt": self._enhance_prompt_with_analysis(text_request, intent_analysis),
            "style_id": optimal_style,
            "project_context": project_context,
            "api_key": self.api_key
        })
        
        return self._present_contextual_result(result, intent_analysis, project_context)
```

### Workflow Orchestration

```python
class CreativeWorkflowManager:
    def __init__(self):
        self.workflow_state = {}
        self.user_preferences = {}
    
    async def orchestrate_creative_project(self, project_type: str, user_requirements: dict):
        """Manage multi-step creative projects."""
        
        if project_type == "brand_identity":
            return await self._brand_identity_workflow(user_requirements)
        elif project_type == "marketing_campaign":
            return await self._marketing_campaign_workflow(user_requirements)
        elif project_type == "product_mockup":
            return await self._product_mockup_workflow(user_requirements)
        
    async def _brand_identity_workflow(self, requirements: dict):
        """Step-by-step brand identity creation."""
        
        # Step 1: Logo concepts
        logo_concepts = await client.call_tool("generate_image_from_text", {
            "prompt": f"logo design for {requirements['business_name']}, {requirements['industry']}",
            # Omit style_id to get multiple style options
            "project_context": {
                "target_audience": requirements.get("target_audience"),
                "mood": requirements.get("brand_personality")
            },
            "api_key": self.api_key
        })
        
        yield {
            "step": "logo_concepts",
            "message": "I've created 4 different logo concepts for your brand:",
            "results": logo_concepts["images"],
            "next_action": "Please select your preferred logo style, and I'll create variations and supporting brand elements."
        }
        
        # Step 2: Wait for user selection, then create brand elements
        user_choice = yield  # Wait for user input
        
        selected_style = user_choice["selected_style"]
        
        # Create brand color palette and supporting elements
        brand_elements = await client.call_tool("generate_image_from_text", {
            "prompt": f"brand color palette and design elements for {requirements['business_name']}",
            "style_id": selected_style,
            "project_context": {
                "brand_colors": self._extract_colors_from_logo(logo_concepts["images"][user_choice["index"]]),
                "target_audience": requirements.get("target_audience"),
                "mood": requirements.get("brand_personality")
            },
            "api_key": self.api_key
        })
        
        yield {
            "step": "brand_elements",
            "message": "Here's your complete brand identity system:",
            "logo": logo_concepts["images"][user_choice["index"]],
            "brand_elements": brand_elements,
            "next_action": "Would you like me to create marketing materials using this brand system?"
        }
```

## Performance Optimization

### Caching and Efficiency

```python
class OptimizedMCPClient:
    def __init__(self):
        self.style_cache = {}
        self.session_cache = {}
        self.context_cache = {}
    
    async def efficient_style_selection(self, user_preference: str, project_context: dict = None):
        """Optimize style selection with caching."""
        
        cache_key = f"{user_preference}_{hash(str(project_context))}"
        
        if cache_key in self.style_cache:
            return self.style_cache[cache_key]
        
        # Get styles only once per session
        if "all_styles" not in self.style_cache:
            all_styles = await client.call_tool("list_styles", {"api_key": self.api_key})
            self.style_cache["all_styles"] = all_styles
        
        # Smart style matching
        optimal_style = self._match_style_to_context(user_preference, project_context, self.style_cache["all_styles"])
        
        self.style_cache[cache_key] = optimal_style
        return optimal_style
    
    async def batch_generation_request(self, requests: list):
        """Handle multiple generation requests efficiently."""
        
        # Group requests by authentication method
        trial_requests = [r for r in requests if r.get("session_id")]
        api_requests = [r for r in requests if r.get("api_key")]
        
        results = []
        
        # Process trial requests with usage tracking
        for request in trial_requests:
            # Check trial status before each request
            trial_status = await self._check_cached_trial_status(request["session_id"])
            if trial_status["can_generate"]:
                result = await self._execute_generation_request(request)
                results.append(result)
            else:
                results.append({"error": "trial_exhausted", "upgrade_options": trial_status["upgrade_options"]})
        
        # Process API requests (unlimited)
        for request in api_requests:
            result = await self._execute_generation_request(request)
            results.append(result)
        
        return results
```

## Testing and Debugging

### MCP Integration Testing

```python
import pytest
from unittest.mock import AsyncMock

class TestMCPIntegration:
    @pytest.fixture
    async def mcp_client(self):
        """Mock MCP client for testing."""
        client = AsyncMock()
        
        # Mock tool responses
        client.call_tool.side_effect = self._mock_tool_responses
        
        return client
    
    def _mock_tool_responses(self, tool_name: str, parameters: dict):
        """Simulate realistic MCP tool responses."""
        
        if tool_name == "start_trial_session":
            return {
                "session_id": "test-trial-123",
                "images_remaining": 5,
                "upgrade_options": []
            }
        
        elif tool_name == "stylize_image":
            if parameters.get("style_id"):
                # Single style response
                return {
                    "stylized_image_url": "https://example.com/stylized.png",
                    "style_applied": parameters["style_id"],
                    "prompt_used": f"test prompt, {parameters['style_id']} style"
                }
            else:
                # Multiple styles response
                return {
                    "multiple_styles": True,
                    "images": [
                        {"style_id": "van_gogh", "style_name": "Van Gogh", "stylized_image_url": "https://example.com/vg.png"},
                        {"style_id": "pixel_art", "style_name": "Pixel Art", "stylized_image_url": "https://example.com/pixel.png"}
                    ],
                    "total_images": 2
                }
        
        elif tool_name == "list_styles":
            return [
                {"id": "van_gogh", "name": "Van Gogh", "description": "Bold brush strokes"},
                {"id": "pixel_art", "name": "Pixel Art", "description": "Retro gaming aesthetic"}
            ]
    
    async def test_conversation_flow(self, mcp_client):
        """Test natural conversation progression."""
        
        # Simulate user asking about capabilities
        workflow = ImageStyleDiscovery()
        workflow.client = mcp_client
        
        response = await workflow.handle_style_inquiry("What can you do with images?")
        
        assert "Van Gogh" in response
        assert "Pixel Art" in response
        assert "Would you like to try" in response
```

## MCP Resources

### Styles Catalog Resource

The server provides a comprehensive styles catalog as an MCP resource:

```python
# Access styles catalog as resource
catalog = await client.get_resource("styles://catalog", {
    "api_key": "your-api-key"
})

# Returns complete JSON catalog with all style information
```

## Production Deployment

### MCP Endpoints

The production MCP server is **live and accessible** at:

**Server-Sent Events (SSE) Transport:**
```
https://stylize-mcp-server-997481449751.us-central1.run.app/mcp/sse
```

**JSON-RPC Transport:**
```
https://stylize-mcp-server-997481449751.us-central1.run.app/mcp
```

### Verified Compatibility

**Tested and working with:**
- Claude Desktop (recommended)
- VS Code + GitHub Copilot 
- Cursor AI Editor
- Other MCP-compatible clients

### Production Configuration Example

```json
{
  "mcpServers": {
    "stylize-production": {
      "transport": {
        "type": "sse",
        "url": "https://stylize-mcp-server-997481449751.us-central1.run.app/mcp/sse"
      },
      "env": {
        "API_KEY": "your-production-api-key"
      }
    }
  }
}
```

## Best Practices

### For AI Assistant Developers

1. **Value-First Approach**: Always demonstrate capabilities before mentioning limitations
2. **Natural Language Integration**: Embed tool calls seamlessly in conversation flow
3. **Progressive Disclosure**: Start with simple features, introduce advanced capabilities based on user engagement
4. **Graceful Limit Handling**: Never abruptly stop service when limits are reached - always provide clear next steps

### For MCP Integration

1. **Start with trial sessions**: Let users explore before requiring signup
2. **Use multi-style generation for exploration**: Omit `style_id` to show variety
3. **Implement intelligent error recovery**: Convert technical errors into helpful user guidance
4. **Cache styles and sessions**: Optimize performance for better user experience
5. **Monitor usage patterns**: Track for optimization opportunities

### Security Considerations

1. **Store API keys securely**: Never expose in client-side code
2. **Use HTTPS only**: All MCP communication must be encrypted
3. **Implement request validation**: Validate all user inputs before processing
4. **Monitor for unusual activity**: Track usage patterns for security
5. **Handle rate limits gracefully**: Implement backoff strategies for API limits

This comprehensive MCP integration guide provides everything needed to successfully integrate the Stylize MCP Server into AI assistant applications, creating natural, user-friendly experiences that maximize the value of professional image generation capabilities.