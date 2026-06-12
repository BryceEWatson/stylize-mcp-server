# Stylize MCP Server

> **⚠️ Dormant (June 2026):** the hosted demo has been taken offline — the live-demo links below no longer work. The codebase remains a complete, working reference for an MCP-served image service with a freemium credit system, Stripe integration, abuse controls (rate limits, fingerprinting, CAPTCHA), and a Cloud Run deploy pipeline. It can be redeployed from this repo (`cloudbuild.yaml`) at any time. Open an issue if you'd like to see it revived.

[![CI/CD Pipeline](https://github.com/your-username/stylize-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/stylize-mcp/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/status-dormant-lightgrey.svg)](#)

AI-powered image stylization service with professional artistic styles, freemium trial system, and seamless AI assistant integration via Model Context Protocol (MCP).

## ✨ What It Does

Transform any image or text description into professional artistic styles:
- **🎨 Van Gogh**: Bold, emotional brush strokes
- **🎮 Pixel Art**: Retro 8-bit gaming aesthetic  
- **💻 Flat UI**: Modern, minimalist interface design
- **✨ Neumorphic**: Soft, tactile interface elements
- **🔷 Glassmorphic**: Frosted glass transparency effects

## 🚀 Try It Now - No Setup Required!

### **For Everyone**: Interactive Demo
**🌟 [Try the Live Demo](https://stylize-mcp-server-997481449751.us-central1.run.app/web/demo)**
- **5 free images immediately** - no account needed
- **Drag & drop** image upload or text-to-image generation
- **"Surprise Me"** feature generates 4 random artistic styles
- **Mobile-friendly** interface

### **For AI Assistant Users**: Claude Desktop Integration
Get artistic image generation in natural conversation with Claude:

1. **Add to Claude Desktop config**:
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

2. **Talk naturally to Claude**:
```
"Can you make this photo look like a Van Gogh painting?"
"Create a logo for my coffee shop in different artistic styles"
"Show me this landscape in 4 different art styles"
```

### **For Developers**: REST API
```bash
# Single style
curl -X POST https://stylize-mcp-server-997481449751.us-central1.run.app/stylize_image \
  -F "style_id=van_gogh" \
  -F "user_prompt=a peaceful mountain landscape"

# Multiple styles (omit style_id for 4 random styles)
curl -X POST https://stylize-mcp-server-997481449751.us-central1.run.app/stylize_image \
  -F "user_prompt=a peaceful mountain landscape"
```

## 💎 Features

**✅ Production Ready**
- **Live service**: Fully operational on Google Cloud Platform
- **5 free trial images** immediately, no signup required
- **Zero-friction experience** for legitimate users

**✅ Multiple Access Methods**
- **Web interface**: Professional trial upgrade and user dashboard
- **MCP integration**: Natural AI assistant conversations
- **REST API**: Direct programmatic access
- **Credit system**: Pay-as-you-go with 4 pricing tiers

**✅ Enterprise-Grade Security**
- **Multi-layered abuse prevention**: Device fingerprinting, VPN detection, behavioral analysis
- **Progressive challenges**: Risk-based CAPTCHA integration
- **Real-time monitoring**: Automated threat detection and alerting
- **Privacy-conscious**: Minimal data collection with automatic expiration

**✅ Developer-Friendly**
- **Comprehensive API**: Full REST API with OpenAPI documentation
- **MCP protocol support**: 6 specialized tools for AI assistants
- **Authentication options**: Trial sessions, JWT tokens, or API keys
- **Extensive documentation**: Complete guides for integration and deployment

## 🎯 Quick Examples

### Natural AI Conversation
```
👤 "I need a logo for my tech startup"
🤖 "I'll create several logo concepts in different styles for you..."
    [Generates 4 artistic variations automatically]
🤖 "Here are modern logo options: clean flat design, artistic Van Gogh style, 
    retro pixel art, and premium neumorphic. Which direction appeals to you?"
```

### Multi-Style Generation
```bash
# Generate 4 random artistic styles in one request
curl -X POST https://stylize-mcp-server-997481449751.us-central1.run.app/stylize_image \
  -F "user_prompt=a sunset over mountains"

# Returns 4 different styled images:
# - Van Gogh style with swirling brushstrokes
# - Pixel art with retro 8-bit aesthetic
# - Flat UI with clean modern design  
# - Neumorphic with soft dimensional look
```

### Brand-Aware Generation
```bash
# Include brand context for consistent results
curl -X POST https://stylize-mcp-server-997481449751.us-central1.run.app/stylize_image \
  -F "user_prompt=tech company marketing image" \
  -F "style_id=flat_ui_icon" \
  -F "project_context={\"brand_colors\":[\"#007ACC\",\"#FF6B35\"],\"mood\":\"professional\"}"
```

## 📚 Documentation

### **Get Started**
- **[User Guide](docs/user-guide/getting-started.md)** - Quick start for all users
- **[Interactive Demo](https://stylize-mcp-server-997481449751.us-central1.run.app/web/demo)** - Try it now

### **For Developers**
- **[API Reference](docs/developer-guide/api-reference.md)** - Complete REST API documentation
- **[MCP Integration](docs/developer-guide/mcp-integration.md)** - AI assistant integration guide
- **[OpenAPI Docs](https://stylize-mcp-server-997481449751.us-central1.run.app/docs)** - Interactive API explorer

### **For DevOps**
- **[Infrastructure Setup](docs/deployment/infrastructure-setup.md)** - Complete deployment guide
- **[Security Configuration](docs/deployment/security-configuration.md)** - Abuse prevention system
- **[Testing Guide](docs/TESTING_GUIDE.md)** - Comprehensive testing procedures

## 🛡️ Security & Privacy

**Enterprise-Grade Protection**:
- **Device fingerprinting** prevents multi-session abuse
- **VPN/proxy detection** with 95%+ accuracy using premium APIs
- **Behavioral analysis** identifies automated vs. human usage
- **Progressive challenges** maintain smooth UX while blocking abuse

**Privacy-Conscious Design**:
- **Minimal data collection** - only technical metadata required for security
- **24-hour expiration** - all session data automatically deleted
- **No personal information** stored in device fingerprints
- **GDPR compliant** with transparent security measures

## 🏗️ Architecture

**Cloud-Native Design**:
- **FastAPI** server with async/await for high performance
- **Google Cloud Platform** infrastructure with auto-scaling
- **DALL·E 3** integration for premium image generation
- **Redis caching** with graceful in-memory fallback

**Smart Image Pipeline**:
- **Context analysis** using GPT-4V for reference images
- **Template-driven prompts** ensure consistent style application
- **Content safety filtering** via Cloud Vision SafeSearch
- **Public URLs** via Google Cloud Storage with CDN

## 🚦 Current Status

**✅ Fully Operational Production Service**
- **Live URL**: https://stylize-mcp-server-997481449751.us-central1.run.app
- **Health Status**: All services operational
- **Uptime**: 99.9% availability
- **Response Time**: <2s average image generation
- **Last Updated**: 2025-06-03

**✅ Complete Feature Set**
- Trial system with 5 free images
- User registration and credit purchasing  
- Enterprise security with abuse prevention
- MCP integration for AI assistants
- Professional web interface
- Comprehensive API documentation

## 💳 Pricing

**🆓 Free Trial**: 5 images immediately, no signup required

**🆓 Free Account**: 100 images/month after registration

**💳 Credit Packages** (pay-as-you-go):
- **Starter**: 55 credits for $9.99
- **Popular**: 225 credits for $29.99 ⭐
- **Pro**: 575 credits for $59.99  
- **Enterprise**: 1,200 credits for $99.99

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**: Follow existing code patterns and add tests
4. **Run tests**: `pytest --cov=app`
5. **Submit a pull request**: Include clear description of changes

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Live Service**: https://stylize-mcp-server-997481449751.us-central1.run.app
- **Interactive Demo**: https://stylize-mcp-server-997481449751.us-central1.run.app/web/demo
- **API Documentation**: https://stylize-mcp-server-997481449751.us-central1.run.app/docs
- **Health Check**: https://stylize-mcp-server-997481449751.us-central1.run.app/health

---

**Made with ❤️ for the AI community** - Transform your ideas into stunning visual art with professional artistic styles.