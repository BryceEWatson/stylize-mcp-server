# 🎨 Stylize MCP Server - Live Demo

> **Try it now:** The Stylize MCP Server is fully operational and ready for public use!

## 🚀 Quick Demo Links

### **Instant Demo (No Setup Required)**
- **🌐 Live API**: https://stylize-mcp-server-997481449751.us-central1.run.app
- **📊 Health Check**: https://stylize-mcp-server-997481449751.us-central1.run.app/health
- **📖 API Docs**: https://stylize-mcp-server-997481449751.us-central1.run.app/docs
- **💎 Free Trial**: 5 images immediately, no signup required!

---

## 🎯 Try These Demo Commands

### **1. Generate Single Style Image**
```bash
curl -X POST https://stylize-mcp-server-997481449751.us-central1.run.app/stylize_image \
  -F "style_id=van_gogh" \
  -F "user_prompt=a majestic mountain landscape at sunset"
```

### **2. Generate Multiple Random Styles** 
```bash
curl -X POST https://stylize-mcp-server-997481449751.us-central1.run.app/stylize_image \
  -F "user_prompt=a cyberpunk city with neon lights"
```

### **3. Check Available Styles**
```bash
curl https://stylize-mcp-server-997481449751.us-central1.run.app/styles
```

### **4. Check Your Trial Status**
```bash
curl https://stylize-mcp-server-997481449751.us-central1.run.app/trial/status
```

---

## 🎨 Available Art Styles

| Style ID | Style Name | Description |
|----------|------------|-------------|
| `van_gogh` | Van Gogh | Post-impressionist with bold, swirling brushstrokes |
| `pixel_art` | Pixel Art | Retro 8-bit video game aesthetic |
| `flat_ui_icon` | Flat UI Icon | Modern, minimalist interface design |
| `neumorphic_button` | Neumorphic | Soft UI with subtle shadows and depth |
| `glassmorphic_card` | Glassmorphic | Translucent glass-like effects |

---

## 🤖 MCP Integration Demo

### **Setup for Claude Desktop**

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

2. **Try these prompts in Claude:**
```
"Start a trial session for image generation"
"Generate an image of a sunset in Van Gogh style"
"Create multiple style variations of a space station"
"What styles are available for image generation?"
```

---

## 📊 Demo Results

### **Single Style Response Example:**
```json
{
  "original_id": "req-abc123",
  "style": "van_gogh", 
  "stylized_image_url": "https://storage.googleapis.com/stylize-variants-bucket/variants/abc123.png",
  "trial_info": {
    "images_used": 1,
    "images_remaining": 4,
    "signup_message": "You have 4 free images remaining. Sign up for 100 free images per month!",
    "signup_url": "/auth/register"
  }
}
```

### **Multiple Styles Response Example:**
```json
{
  "original_id": "req-def456",
  "multiple_styles": true,
  "images": [
    {
      "style_id": "van_gogh",
      "style_name": "Van Gogh", 
      "stylized_image_url": "https://storage.googleapis.com/...",
      "prompt_used": "a cyberpunk city with neon lights, in the style of Vincent van Gogh..."
    },
    {
      "style_id": "pixel_art",
      "style_name": "Pixel Art",
      "stylized_image_url": "https://storage.googleapis.com/...", 
      "prompt_used": "a cyberpunk city with neon lights, as retro pixel art..."
    }
  ],
  "total_images": 4,
  "trial_info": {
    "images_used": 5,
    "images_remaining": 0
  }
}
```

---

## 🔐 Authentication Demo

### **1. Create Free Account** 
```bash
curl -X POST https://stylize-mcp-server-997481449751.us-central1.run.app/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@example.com",
    "password": "demopass123",
    "first_name": "Demo", 
    "last_name": "User"
  }'
```

### **2. Generate API Key**
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -X POST https://stylize-mcp-server-997481449751.us-central1.run.app/user/api-keys \
  -d '{"name": "Demo Integration"}'
```

### **3. Use API Key**
```bash
curl -X POST https://stylize-mcp-server-997481449751.us-central1.run.app/stylize_image \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "style_id=pixel_art" \
  -F "user_prompt=a dragon flying over a castle"
```

---

## 📈 Performance & Limits

| Feature | Limit | Notes |
|---------|-------|-------|
| **Trial Images** | 5 free | No signup required |
| **Free Tier** | 100/month | After registration |
| **Image Size** | 10MB max | JPEG/PNG only |
| **Generation Time** | ~10-15 seconds | Includes DALL·E 3 processing |
| **Uptime** | 99.9%+ | Google Cloud Run |
| **Rate Limits** | 60 requests/min | Per IP address |

---

## 🛠️ Integration Examples

### **Python Example**
```python
import requests

response = requests.post(
    "https://stylize-mcp-server-997481449751.us-central1.run.app/stylize_image",
    data={
        "style_id": "van_gogh",
        "user_prompt": "a peaceful garden with cherry blossoms"
    }
)

result = response.json()
print(f"Generated image: {result['stylized_image_url']}")
```

### **JavaScript/Node.js Example**
```javascript
const FormData = require('form-data');
const fetch = require('node-fetch');

const form = new FormData();
form.append('user_prompt', 'a futuristic robot in a forest');

const response = await fetch(
  'https://stylize-mcp-server-997481449751.us-central1.run.app/stylize_image',
  { method: 'POST', body: form }
);

const result = await response.json();
console.log('Generated images:', result.images);
```

### **cURL with File Upload**
```bash
curl -X POST https://stylize-mcp-server-997481449751.us-central1.run.app/stylize_image \
  -F "image=@your-photo.jpg" \
  -F "style_id=glassmorphic_card" \
  -F "user_prompt=transform this into a modern glass interface element"
```

---

## 🎊 What Makes This Demo Special

✅ **Production-Ready**: Real deployment, not just a prototype  
✅ **No Setup Required**: Try immediately with trial system  
✅ **Multiple Interfaces**: REST API + MCP Protocol  
✅ **Enterprise Features**: Authentication, rate limiting, monitoring  
✅ **High Quality**: DALL·E 3 integration with curated prompts  
✅ **Cost-Optimized**: Intelligent caching and usage controls  

---

## 🚀 Ready to Build Your Own?

1. **Clone the repo**: `git clone https://github.com/your-username/stylize-mcp`
2. **Deploy to GCP**: Use included Terraform config
3. **Customize styles**: Edit `app/styles.json`
4. **Scale up**: Add more styles, users, features

**Full documentation**: [README.md](./README.md) | **Setup guide**: [QUICK_START.md](./QUICK_START.md)