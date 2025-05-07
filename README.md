# Stylize MCP Server MVP

## Overview

The Stylize MCP Server is a cloud-based service that transforms user-supplied images into multiple style-specific variants. It leverages generative-image APIs (DALL·E 3, Vertex AI Imagen, EverArt) with a curated style bank, template-driven prompt engineering, content-safety filtering, and intelligent caching to deliver high-quality stylized images efficiently.

## MVP Goals

- Implement a REST API endpoint for image stylization (`POST /stylize_image`)
- Support curated style catalog with UI/icon-specific styles
- Integrate with DALL·E 3 for image generation
- Implement content safety filtering with Cloud Vision SafeSearch
- Provide intelligent caching to improve performance and reduce costs
- Establish cost guardrails with daily caps and per-user quotas
- Set up infrastructure as code (IaC) using Terraform on Google Cloud Platform

## Local Development Setup

### Prerequisites

- Python 3.10 or newer
- pip (Python package manager)
- Google Cloud SDK (for local GCP service emulation)
- OpenAI API key (for DALL·E 3 integration)

### Environment Setup

```bash
# Clone the repository
git clone [repository_url]
cd stylize-mcp-server

# Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables (copy .env.example to .env and edit)
# Add your OpenAI API key and other configuration
```

### Running the Server Locally

```bash
# Start the FastAPI server
uvicorn app.main:app --reload

# The server will be available at http://localhost:8000
# API documentation is available at http://localhost:8000/docs
```

## Project Structure

- `app/`: Application code
- `infra/`: Terraform infrastructure as code
- `docs/`: Project documentation

## API Endpoints (MVP)

- `POST /stylize_image`: Stylize an uploaded image with specified style
- `GET /styles`: List available styles
- `GET /health`: Server health check
- `GET /mcp`: MCP server endpoint for Server-Sent Events (SSE)

## MCP Server Access

The Stylize MCP Server exposes a FastMCP endpoint that can be accessed through Server-Sent Events (SSE). This allows clients to interact with the available MCP tools in real-time.

### Local Testing

When running the server locally, the MCP server can be accessed at:
```
http://localhost:8080/mcp
```

The MCP server currently provides the following tools:
- `stylize_image_mcp_tool`: Takes an image (as bytes) and a style ID, and returns a URL to the stylized image
