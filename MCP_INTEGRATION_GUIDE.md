# MCP Integration Guide for AI Assistants

This guide provides comprehensive documentation for integrating the Stylize MCP Server into AI assistant applications, focusing on the user experience and natural conversation flows.

## Overview

The Stylize MCP Server is designed to enhance AI assistants with professional-grade image generation and stylization capabilities. Rather than requiring users to learn technical APIs, AI assistants can seamlessly integrate these capabilities into natural conversations.

## Quick Start Integration

### 1. MCP Server Configuration

**Claude Desktop Configuration** (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "stylize": {
      "command": "node",
      "args": ["path/to/mcp-client.js"],
      "env": {
        "SERVER_URL": "https://stylize-mcp-server-997481449751.us-central1.run.app/mcp",
        "API_KEY": "your-api-key-here"
      }
    }
  }
}
```

**Direct MCP Connection**:
```python
import mcp_client

client = mcp_client.connect("https://stylize-mcp-server-997481449751.us-central1.run.app/mcp")
tools = await client.list_tools()
# Available: stylize_image, generate_image_from_text, list_styles, get_style_details, start_trial_session, check_trial_status
```

### 2. Authentication Modes

**API Key Mode** (For production AI assistants):
```python
# Full access with API key
result = await client.call_tool("stylize_image", {
    "image_base64": "...",
    "style_id": "van_gogh",
    "api_key": "your-production-key"
})
```

**Trial Mode** (For anonymous/new users):
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

## Natural Conversation Patterns

### Pattern 1: Discovery-Driven Exploration

This pattern helps users discover capabilities through natural conversation:

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
    
    async def _multi_style_generation(self, request: str, image=None):
        """Offer style variety and options."""
        if image:
            result = await client.call_tool("stylize_image", {
                "image_base64": image,
                # Omit style_id for multiple styles
                "session_id": self.session_id
            })
        else:
            result = await client.call_tool("generate_image_from_text", {
                "prompt": request,
                # Omit style_id for multiple styles  
                "api_key": self.api_key
            })
        
        return f"""I've created {result['total_images']} different style variations for you:

{self._format_multiple_results(result['images'])}

Which direction do you like? I can refine any of these further or try additional variations."""
    
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
    
    def _format_credit_packages(self, packages):
        """Format credit packages for conversational presentation."""
        formatted = []
        for pkg in packages:
            if pkg.get("popular"):
                formatted.append(f"   ⭐ **{pkg['name']}**: {pkg['credits']} credits for ${pkg['price']} (Most Popular)")
            else:
                formatted.append(f"   • **{pkg['name']}**: {pkg['credits']} credits for ${pkg['price']}")
        return "\n".join(formatted)
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
    
    async def _analyze_reference_images(self, images: list) -> dict:
        """Extract visual context from reference images."""
        # Use the stylize_image tool for context analysis
        # This leverages the GPT-4V context analysis built into the server
        
        context_elements = []
        for img in images:
            # Use stylize_image with a neutral prompt to get context analysis
            analysis_result = await client.call_tool("stylize_image", {
                "image_base64": img,
                "style_id": "flat_ui_icon",  # Use flat style to see structure clearly
                "user_prompt": "analyze visual elements and composition",
                "api_key": self.api_key
            })
            
            # Extract context from the prompt that was generated
            context_elements.append(self._extract_context_from_prompt(analysis_result.get("prompt_used", "")))
        
        return self._synthesize_visual_context(context_elements)
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
    
    async def _check_cached_trial_status(self, session_id: str):
        """Cache trial status to avoid repeated API calls."""
        cache_key = f"trial_status_{session_id}"
        
        if cache_key in self.session_cache:
            cached_status = self.session_cache[cache_key]
            # Cache for 30 seconds to balance accuracy and performance
            if time.time() - cached_status["timestamp"] < 30:
                return cached_status["data"]
        
        # Fetch fresh status
        status = await client.call_tool("check_trial_status", {"session_id": session_id})
        
        self.session_cache[cache_key] = {
            "data": status,
            "timestamp": time.time()
        }
        
        return status
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
    
    async def test_trial_progression(self, mcp_client):
        """Test trial usage and conversion flow."""
        
        handler = ProgressiveImageGeneration()
        handler.client = mcp_client
        handler.session_id = "test-trial-123"
        
        # Simulate multiple generations
        for i in range(5):
            result = await handler._simple_generation("test image", "test_image_data")
            assert "style image" in result
        
        # Test trial exhaustion
        mcp_client.call_tool.side_effect = lambda tool, params: {"error": "trial_exhausted"}
        
        error_handler = ErrorRecoveryHandler()
        error_handler.client = mcp_client
        
        response = await error_handler.handle_trial_limit("create another image")
        assert "Free Account" in response
        assert "Credit Packages" in response
```

## Deployment Considerations

### Production Integration Checklist

- [ ] **Authentication Setup**: Configure API keys for production use
- [ ] **Error Handling**: Implement comprehensive error recovery patterns
- [ ] **Rate Limiting**: Handle MCP server rate limits gracefully
- [ ] **Caching Strategy**: Cache styles and session data for performance
- [ ] **User Experience**: Test conversation flows with real users
- [ ] **Monitoring**: Track tool usage and error rates
- [ ] **Fallback Behavior**: Handle MCP server unavailability
- [ ] **Documentation**: Provide clear usage examples for your team

### Monitoring and Analytics

```python
class MCPUsageTracker:
    def __init__(self):
        self.metrics = {}
        
    async def track_tool_usage(self, tool_name: str, parameters: dict, result: dict, execution_time: float):
        """Track MCP tool usage for optimization."""
        
        metric_key = f"mcp_tool_{tool_name}"
        
        if metric_key not in self.metrics:
            self.metrics[metric_key] = {
                "total_calls": 0,
                "total_time": 0,
                "success_count": 0,
                "error_count": 0,
                "parameter_patterns": {}
            }
        
        self.metrics[metric_key]["total_calls"] += 1
        self.metrics[metric_key]["total_time"] += execution_time
        
        if "error" in result:
            self.metrics[metric_key]["error_count"] += 1
        else:
            self.metrics[metric_key]["success_count"] += 1
        
        # Track parameter patterns for optimization
        for param, value in parameters.items():
            if param not in self.metrics[metric_key]["parameter_patterns"]:
                self.metrics[metric_key]["parameter_patterns"][param] = {}
            
            value_str = str(value)[:50]  # Truncate for privacy
            self.metrics[metric_key]["parameter_patterns"][param][value_str] = \
                self.metrics[metric_key]["parameter_patterns"][param].get(value_str, 0) + 1
    
    def get_optimization_suggestions(self) -> list:
        """Analyze metrics to suggest optimizations."""
        suggestions = []
        
        for tool_name, metrics in self.metrics.items():
            avg_time = metrics["total_time"] / metrics["total_calls"]
            error_rate = metrics["error_count"] / metrics["total_calls"]
            
            if avg_time > 5.0:  # 5 second threshold
                suggestions.append(f"{tool_name}: Consider caching (avg time: {avg_time:.2f}s)")
            
            if error_rate > 0.1:  # 10% error threshold
                suggestions.append(f"{tool_name}: High error rate ({error_rate:.1%}) - review error handling")
        
        return suggestions
```

This comprehensive integration guide provides everything needed to properly integrate the Stylize MCP Server into AI assistant applications, focusing on creating natural, user-friendly experiences while maximizing the value of the image generation capabilities.