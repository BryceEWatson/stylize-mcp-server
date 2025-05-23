# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Running the Application
```bash
# Activate virtual environment first
python -m venv venv
source venv/bin/activate  # On Unix/macOS
venv\Scripts\activate     # On Windows

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

## Deployment Information

### Cloud Run Deployment
- **Service Name**: `stylize-mcp-server`
- **Region**: `us-central1`
- **Project**: `stylize-mcp-server` (GCP project ID: 997481449751)
- **URL**: https://stylize-mcp-server-997481449751.us-central1.run.app
- **Current Revision**: `stylize-mcp-server-00023-9rn`
- **Image**: `us-central1-docker.pkg.dev/stylize-mcp-server/stylize-repo/stylize-mcp-server:b285416500d2a181a70a6360778ef9f3f0f2bd96`

### Monitoring and Logs
```bash
# View Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=stylize-mcp-server AND resource.labels.location=us-central1" --limit=20 --format="table(timestamp,severity,textPayload)"

# Get service details
gcloud run services describe stylize-mcp-server --region=us-central1
```

### Known Issues
- **GCS Signed URL Generation**: Service currently fails to generate signed URLs due to credential type mismatch
  - Error: Service account needs private key credentials but is using Compute Engine credentials (token-only)
  - Affects: `/stylize_image` endpoint returns 500 errors after successful image generation
  - Impact: Images are generated and uploaded to GCS but signed download URLs cannot be created

## Development Best Practices
- Always activate the venv before installing libraries