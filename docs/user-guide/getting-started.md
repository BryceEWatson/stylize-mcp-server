# Getting Started with Stylize MCP Server

## 🚀 Ready to Use - No Setup Required!

The Stylize MCP Server is **live and fully operational**. Get started in minutes with **5 free images** - no account needed!

## 🎯 Choose Your Experience

### Option 1: AI Assistant Integration (Recommended) 🤖

**Perfect for:** Natural conversation-based image creation with Claude, ChatGPT, or other AI assistants

**Setup Time:** 2 minutes  
**Free Trial:** 5 images immediately, no signup required

#### Step 1: Configure Claude Desktop

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

#### Step 2: Start Natural Conversations! 

**No technical knowledge needed** - just talk to Claude naturally:

##### **Beginner Examples**
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

##### **Creative Project Examples**
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

### Option 2: Web Interface (Traditional) 🌐

**Perfect for:** Direct access without AI assistant integration

#### Instant Free Trial
- **Try Now**: https://stylize-mcp-server-997481449751.us-central1.run.app/web/demo
- **5 free images** immediately, no account required
- **Beautiful web interface** with professional forms

#### User Dashboard  
- **Dashboard**: https://stylize-mcp-server-997481449751.us-central1.run.app/web/dashboard
- **Create account** for 100 free images/month
- **Purchase credits** with 4 pricing tiers ($9.99 - $99.99)
- **Mobile-responsive** design

### Option 3: Direct REST API (For Developers) ⚡

**Perfect for:** Direct integration into applications or testing

#### Instant Trial Access
```bash
# Check service health
curl https://stylize-mcp-server-997481449751.us-central1.run.app/health

# Single style generation (uses 1 trial image)
curl -X POST https://stylize-mcp-server-997481449751.us-central1.run.app/stylize_image \
  -F "style_id=van_gogh" \
  -F "user_prompt=a peaceful mountain landscape"

# Multi-style generation (uses 4 trial images - omit style_id)
curl -X POST https://stylize-mcp-server-997481449751.us-central1.run.app/stylize_image \
  -F "user_prompt=a peaceful mountain landscape"

# Check available styles
curl https://stylize-mcp-server-997481449751.us-central1.run.app/styles
```

## 🎨 Available Creative Styles

| Style | Best For | Example Use Cases |
|-------|----------|-------------------|
| **🎨 Van Gogh** | Artistic expression, emotional impact | Art projects, creative websites, expressive branding |
| **🎮 Pixel Art** | Retro/gaming themes, nostalgic brands | Game assets, retro websites, nostalgic marketing |
| **💻 Flat UI Icon** | Modern apps, clean branding | App icons, web interfaces, minimalist logos |  
| **✨ Neumorphic** | Premium, tactile interfaces | High-end product design, luxury branding |
| **🔷 Glassmorphic** | Cutting-edge, modern designs | Tech products, futuristic interfaces |

## 🚀 What Happens Next?

### During Your Trial (5 Free Images)
- **Images 1-3**: Focus on exploring and creating
- **Images 4-5**: Get gentle reminders about remaining usage
- **After 5**: Friendly upgrade options appear

### Upgrade Paths
- **🆓 Free Account**: Sign up for 100 images/month
- **💳 Credit Packages**: $9.99 - $99.99 for unlimited usage
- **🏢 Enterprise**: Custom solutions for teams

## 💡 Pro Tips for Best Results

### **For AI Assistant Users**
- **Be Specific**: "Create a logo for a tech startup" vs "Create a logo"
- **Mention Style Preferences**: "I like clean, modern designs" 
- **Upload Reference Images**: Help AI understand your vision
- **Ask for Variations**: "Show me this in different styles"

### **For API Users**
- **Omit `style_id`** to get 4 random styles for exploration
- **Include `user_prompt`** for better results: "a sunset over mountains"
- **Use `project_context`** for brand-aware generation
- **Monitor trial usage** with `/trial/status` endpoint

### **Example: Brand-Aware Generation**
```bash
curl -X POST https://stylize-mcp-server-997481449751.us-central1.run.app/stylize_image \
  -F "user_prompt=modern tech company logo" \
  -F "style_id=flat_ui_icon" \
  -F "project_context={\"brand_colors\":[\"#007ACC\",\"#FF6B35\"],\"mood\":\"professional\",\"target_audience\":\"tech professionals\"}"
```

## 🛠️ How AI Assistants Use These Tools

**Behind the scenes, when you chat with Claude:**

1. **`start_trial_session()`** → Gets you 5 free images
2. **`stylize_image()`** → Transforms your uploaded photos  
3. **`generate_image_from_text()`** → Creates new images from descriptions
4. **`list_styles()`** → Shows available artistic styles
5. **`check_trial_status()`** → Tracks usage and guides upgrades

**You just have natural conversations - Claude handles all the technical details!**

## 📚 Next Steps

**New to MCP?**
- See our **[MCP Integration Guide](../developer-guide/mcp-integration.md)** for detailed patterns
- Check the **[API Reference](../developer-guide/api-reference.md)** for complete documentation

**Need More Details?**
- **API Documentation**: https://stylize-mcp-server-997481449751.us-central1.run.app/docs
- **Interactive Demo**: https://stylize-mcp-server-997481449751.us-central1.run.app/web/demo

**Ready to Integrate?**
- **For Developers**: See [Developer Guide](../developer-guide/)
- **For Enterprise**: Contact for custom solutions

---

## 🎉 Start Creating Now!

**Easiest:** Configure Claude Desktop and start chatting  
**Fastest:** Try the web interface for immediate access  
**Most Flexible:** Use the REST API for custom integration

**Remember:** 5 free images to start, 100/month with free account, unlimited with credits!