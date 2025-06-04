# Infrastructure Setup Guide

Complete guide for setting up the Stylize MCP Server infrastructure from development to production.

## Quick Setup Options

### Option 1: Use Production Service (Recommended)
The easiest way to get started - use our live production service:
- **URL**: https://stylize-mcp-server-997481449751.us-central1.run.app
- **Status**: Fully operational
- **Trial**: 5 free images, no account required
- **Setup Time**: 2 minutes for MCP integration

### Option 2: Local Development
For local development and testing:
```bash
# Clone and setup
git clone [repository_url]
cd stylize-mcp-server
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
export AUTH_DEV_BYPASS=true
export DEV_API_KEY=test-key-123
export OPENAI_API_KEY=your_openai_key

# Run locally
uvicorn app.main:app --reload
```

### Option 3: Full Infrastructure Deployment
Deploy your own instance to Google Cloud Platform.

## Local Development Setup

### Prerequisites
- Python 3.10 or newer
- pip (Python package manager)
- OpenAI API key
- Optional: Google Cloud SDK (for GCP integration)

### Environment Setup

```bash
# Clone the repository
git clone [repository_url]
cd stylize-mcp-server

# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux  
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

#### Required for Local Development
```bash
# OpenAI Integration
OPENAI_API_KEY=your_openai_api_key_here

# Authentication (Development Mode)
AUTH_DEV_BYPASS=true
DEV_API_KEY=test-key-123
```

#### Optional Configuration
```bash
# Security & Abuse Prevention
SECURITY_ENABLED=false               # Disable for local development
AUTH_ENABLED=true                   # Enable authentication

# Google Cloud (if testing GCP integration)
GCP_PROJECT_ID=your_project_id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# Rate Limiting (Development Settings)
TRIAL_CREATION_PER_IP=10           # Higher limits for testing
GLOBAL_DAILY_LIMIT=1000            # Generous limits for development

# Optional: Redis (will fall back to in-memory if not available)
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Running the Server

```bash
# Start the FastAPI server
uvicorn app.main:app --reload

# The server will be available at:
# - API: http://localhost:8000
# - Documentation: http://localhost:8000/docs
# - Health Check: http://localhost:8000/health
```

### Testing Local Setup

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test trial image generation
curl -X POST http://localhost:8000/stylize_image \
  -F "style_id=van_gogh" \
  -F "user_prompt=a beautiful sunset"

# Test with authentication
curl -H "Authorization: Bearer test-key-123" \
     -X POST http://localhost:8000/stylize_image \
     -F "style_id=pixel_art" \
     -F "user_prompt=a retro spaceship"
```

## Production Infrastructure Deployment

### Prerequisites for GCP Deployment

- Google Cloud Platform account with billing enabled
- gcloud CLI installed and configured
- Terraform >= 1.0 installed
- GitHub repository set up
- OpenAI API key

### Step 1: Initial Infrastructure Setup

```bash
# Clone repository
git clone [repository_url]
cd stylize-mcp-server/infra

# Configure Terraform variables
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values:
# project_id = "your-gcp-project-id"
# region = "us-central1"
# github_repo = "your-username/stylize-mcp-server"

# Initialize and deploy
terraform init
terraform plan
terraform apply
```

### Step 2: Manual Configuration Steps

#### Secret Management
For security, API keys must be manually added to Secret Manager:

```bash
# Add OpenAI API key
echo -n "YOUR_ACTUAL_OPENAI_API_KEY" | gcloud secrets versions add OPENAI_API_KEY --data-file=- --project=[PROJECT_ID]

# Optional: Add VPN detection API keys for enhanced security
echo -n "YOUR_IPQUALITYSCORE_KEY" | gcloud secrets versions add IPQUALITYSCORE_API_KEY --data-file=- --project=[PROJECT_ID]
echo -n "YOUR_PROXYCHECK_KEY" | gcloud secrets versions add PROXYCHECK_API_KEY --data-file=- --project=[PROJECT_ID]
```

#### Artifact Registry Setup
```bash
# Create Docker repository (if not done via Terraform)
gcloud artifacts repositories create stylize-repo \
  --repository-format=docker \
  --location=us-central1 \
  --description="Docker repository for Stylize MCP Server images" \
  --project=[PROJECT_ID]
```

#### Cloud Build Configuration
```bash
# Get the Cloud Build service account email
CLOUD_BUILD_SA="$(gcloud projects describe [PROJECT_ID] --format='value(projectNumber)')@cloudbuild.gserviceaccount.com"

# Grant required IAM permissions
gcloud projects add-iam-policy-binding [PROJECT_ID] \
  --member="serviceAccount:${CLOUD_BUILD_SA}" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding [PROJECT_ID] \
  --member="serviceAccount:${CLOUD_BUILD_SA}" \
  --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding [PROJECT_ID] \
  --member="serviceAccount:${CLOUD_BUILD_SA}" \
  --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding [PROJECT_ID] \
  --member="serviceAccount:${CLOUD_BUILD_SA}" \
  --role="roles/secretmanager.secretAccessor"
```

#### CI/CD Pipeline Setup
```bash
# Create Cloud Build trigger
gcloud builds triggers create github \
  --name=stylize-mcp-server-deploy \
  --repo=https://github.com/[YOUR_GITHUB_USERNAME]/stylize-mcp-server \
  --branch-pattern=^main$ \
  --build-config=cloudbuild.yaml \
  --repo-type=GITHUB \
  --substitutions=_REGION=us-central1,_ARTIFACT_REPO_NAME=stylize-repo,_SERVICE_NAME=stylize-mcp-server \
  --project=[PROJECT_ID]
```

### Step 3: Budget and Monitoring Setup

```bash
# Set up billing budget alerts
gcloud beta billing budgets create \
  --billing-account=[BILLING_ACCOUNT_ID] \
  --display-name="Stylize MCP Server Budget" \
  --budget-amount=50USD \
  --threshold-rules=percent=0.5,basis=current_spend \
  --threshold-rules=percent=0.9,basis=current_spend \
  --threshold-rules=percent=1.0,basis=current_spend \
  --email-recipients=[YOUR_EMAIL] \
  --projects=projects/[PROJECT_ID]
```

### Step 4: Production Environment Variables

Configure these in Cloud Run environment variables:

#### Core Configuration
```bash
# Authentication
AUTH_ENABLED=true
API_KEYS_SECRET_PATH=api-keys

# GCP Integration
GCP_PROJECT_ID=[YOUR_PROJECT_ID]
OPENAI_API_KEY_SECRET_PATH=projects/[PROJECT_ID]/secrets/OPENAI_API_KEY/versions/latest

# Storage
GCS_BUCKET_NAME=[YOUR_PROJECT_ID]-stylize-images

# Security & Abuse Prevention
SECURITY_ENABLED=true
HIGH_RISK_THRESHOLD=0.7
FINGERPRINTING_ENABLED=true
```

#### Optional Enhanced Security
```bash
# VPN Detection APIs
VPN_DETECTION_PAID_APIS=true
IPQUALITYSCORE_API_KEY_SECRET_PATH=projects/[PROJECT_ID]/secrets/IPQUALITYSCORE_API_KEY/versions/latest
PROXYCHECK_API_KEY_SECRET_PATH=projects/[PROJECT_ID]/secrets/PROXYCHECK_API_KEY/versions/latest

# CAPTCHA Integration
RECAPTCHA_SITE_KEY=your_recaptcha_site_key
RECAPTCHA_SECRET_KEY_SECRET_PATH=projects/[PROJECT_ID]/secrets/RECAPTCHA_SECRET_KEY/versions/latest

# Rate Limiting (Production Values)
TRIAL_CREATION_PER_IP=5
TRIAL_CREATION_PER_DEVICE=3
IMAGE_GENERATION_PER_SESSION=5
GLOBAL_DAILY_LIMIT=10000
```

## API Key Management

### Creating the First Admin Key

```bash
# Create initial admin API key using the CLI utility
python manage_api_keys.py create "Admin Key" --permissions admin stylize styles mcp
```

### Self-Service API Keys

Once the system is running, users can create their own API keys:

1. **Register for free account**: `/auth/register`
2. **Generate API key**: `/user/api-keys` endpoint
3. **Use immediately**: All endpoints available based on subscription

### Enterprise API Key Management

```bash
# Create API key for enterprise client
curl -H "Authorization: Bearer admin-api-key" \
     -X POST https://your-domain/admin/api-keys \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Enterprise Client",
       "permissions": ["stylize", "styles", "mcp"]
     }'

# List all API keys
curl -H "Authorization: Bearer admin-api-key" \
     -X GET https://your-domain/admin/api-keys

# Deactivate API key
curl -H "Authorization: Bearer admin-api-key" \
     -X DELETE https://your-domain/admin/api-keys/key-abc123
```

## Verification and Testing

### Deployment Verification Checklist

- [ ] **Health Check**: `/health` endpoint returns 200
- [ ] **Trial Generation**: Anonymous image generation works
- [ ] **Authentication**: API key authentication works
- [ ] **User Registration**: Account creation and login works
- [ ] **Credit System**: Credit purchase flow works
- [ ] **MCP Integration**: MCP endpoints respond correctly
- [ ] **Security**: Rate limiting and abuse prevention active
- [ ] **Monitoring**: Logs and metrics are being collected

### Test Commands

```bash
# Health check
curl https://your-domain/health

# Test trial generation
curl -X POST https://your-domain/stylize_image \
  -F "style_id=van_gogh" \
  -F "user_prompt=test image"

# Test authenticated generation
curl -H "Authorization: Bearer your-api-key" \
     -X POST https://your-domain/stylize_image \
     -F "style_id=pixel_art" \
     -F "user_prompt=test authenticated image"

# Test MCP endpoint
curl https://your-domain/mcp/sse

# Test user registration
curl -X POST https://your-domain/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123",
    "first_name": "Test",
    "last_name": "User"
  }'
```

## Monitoring and Maintenance

### Log Monitoring
```bash
# View Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=stylize-mcp-server" --limit=50

# Monitor error logs
gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" --limit=20
```

### Performance Monitoring
```bash
# Get service metrics
gcloud run services describe stylize-mcp-server --region=us-central1

# Monitor security metrics
curl -H "Authorization: Bearer admin-api-key" \
     https://your-domain/admin/security/metrics
```

### Scaling Configuration
```bash
# Update Cloud Run scaling settings
gcloud run services update stylize-mcp-server \
  --region=us-central1 \
  --min-instances=1 \
  --max-instances=10 \
  --cpu=1 \
  --memory=2Gi \
  --concurrency=100
```

## Troubleshooting

### Common Issues

#### Authentication Errors
```bash
# Check if API keys are properly configured
python manage_api_keys.py list

# Verify secret access
gcloud secrets versions access latest --secret="OPENAI_API_KEY"
```

#### Image Generation Failures
```bash
# Check OpenAI API key
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models

# Verify GCS bucket permissions
gsutil ls gs://your-bucket-name
```

#### MCP Connection Issues
```bash
# Test MCP endpoint directly
curl -X POST https://your-domain/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "initialize", "id": 1}'
```

### Performance Optimization

#### Redis Cache Setup
```bash
# Set up Redis for production caching
# In Cloud Console: Create Memorystore Redis instance
# Update environment variables:
REDIS_HOST=your-redis-instance-ip
REDIS_PORT=6379
```

#### CDN Configuration
```bash
# Set up Cloud CDN for image delivery
gcloud compute backend-services create stylize-backend \
  --global \
  --load-balancing-scheme=EXTERNAL

# Configure CDN for GCS bucket
gcloud compute url-maps create stylize-url-map \
  --default-backend-bucket=your-bucket-name
```

## Security Best Practices

### Production Security Checklist

- [ ] **API Keys**: Stored in Secret Manager, never in code
- [ ] **HTTPS Only**: All communication encrypted
- [ ] **Rate Limiting**: Enabled and configured appropriately
- [ ] **VPN Detection**: Enabled for trial abuse prevention
- [ ] **CAPTCHA**: Configured for high-risk requests
- [ ] **Monitoring**: Security metrics and alerts configured
- [ ] **Backup**: Regular database and configuration backups
- [ ] **Updates**: Regular dependency and security updates

### Security Configuration
```bash
# Enable comprehensive security
SECURITY_ENABLED=true
HIGH_RISK_THRESHOLD=0.7
FINGERPRINTING_ENABLED=true
VPN_DETECTION_PAID_APIS=true

# Configure monitoring
ABUSE_LOG_LEVEL=INFO
SECURITY_METRICS_ENABLED=true
```

This infrastructure setup guide provides everything needed to deploy and maintain the Stylize MCP Server from development through production. Follow the appropriate path based on your needs - use the production service for quick integration, local development for testing, or full deployment for custom instances.