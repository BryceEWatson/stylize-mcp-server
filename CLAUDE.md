# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Running the Application
```bash
# Install dependencies
pip install -r requirements.txt

# Run server locally
uvicorn app.main:app --reload

# Run with specific port
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_main.py

# Run tests with verbose output
pytest -v
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
1. **REST API** for image stylization (`/stylize_image`), style management (`/styles`), and health checks
2. **MCP Server** endpoint at `/mcp` for AI agent integration via FastMCP
3. **Two-stage image generation pipeline**:
   - Context analysis using GPT-4V when reference images are provided
   - Prompt generation and image creation using DALL·E 3
   - Results are cached in Redis and stored in GCS

### Service Dependencies
- **OpenAI API**: GPT-4V for analysis, DALL·E 3 for generation
- **Google Cloud Storage**: Image persistence
- **Firestore**: Style catalog and usage tracking
- **Cloud Vision API**: SafeSearch content filtering
- **Redis (Memorystore)**: Response caching
- **Secret Manager**: API key storage

### Key Implementation Details
- The application supports context-aware generation through a `ProjectContext` model for brand consistency
- Image generation includes automatic SafeSearch filtering for uploaded content
- Cost controls are implemented via daily global caps and per-user quotas tracked in Firestore
- The style catalog currently uses a JSON file (`app/styles.json`) with 5 predefined styles

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