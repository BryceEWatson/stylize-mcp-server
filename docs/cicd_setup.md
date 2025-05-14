# Cloud Build CI/CD Pipeline Setup

This document outlines the manual steps required to set up the Cloud Build CI/CD pipeline for the Stylize MCP Server MVP project.

## Prerequisites

Before setting up the CI/CD pipeline, ensure that:

1. The Terraform infrastructure has been applied successfully
2. You have appropriate IAM permissions to create Artifact Registry repositories and Cloud Build triggers

## Manual Setup Steps

### 1. Create Artifact Registry Repository

If not already created through Terraform, create an Artifact Registry Docker repository to store our container images using the following gcloud command:

```bash
gcloud artifacts repositories create stylize-repo \
  --repository-format=docker \
  --location=us-central1 \
  --description="Docker repository for Stylize MCP Server images" \
  --project=[PROJECT_ID]
```

Replace `[PROJECT_ID]` with your actual GCP Project ID (e.g., `stylize-mcp-server`).

> **Note**: This command can be run directly by the human operator to programmatically create the repository without using the GCP Console.

### 2. Connect Cloud Build to GitHub Repository

1. Go to the Cloud Build section in the Google Cloud Console
2. Navigate to "Triggers"
3. Click "Connect Repository"
4. Select GitHub as the source
5. Authenticate with GitHub and select the repository containing the Stylize MCP Server code
6. Follow the prompts to complete the connection

### 3. Create Cloud Build Trigger

#### Option 1: Using the Google Cloud Console (UI)

1. In the Cloud Build section, click "Create Trigger"
2. Configure the trigger with the following settings:
   - Name: `stylize-mcp-server-deploy`
   - Event: Choose "Push to a branch"
   - Source: Select your connected GitHub repository
   - Branch: `^main$` (regular expression to match only the main branch)
   - Configuration: Select "Cloud Build configuration file (yaml or json)"
   - Location: Repository
   - Cloud Build configuration file location: `/cloudbuild.yaml`
3. Add the following substitution variables:
   - `_REGION`: `us-central1`
   - `_ARTIFACT_REPO_NAME`: `stylize-repo`
   - `_SERVICE_NAME`: `stylize-mcp-server`
   - `_OPENAI_API_KEY_SECRET_PATH`: `projects/[PROJECT_ID]/secrets/OPENAI_API_KEY/versions/latest`
     (Replace `[PROJECT_ID]` with your actual GCP Project ID)
4. Click "Create" to finalize the trigger

#### Option 2: Using gcloud CLI (Recommended for Automation)

To programmatically create the Cloud Build trigger, use the following command:

```bash
# First, check if you have a GitHub connection already established
gcloud alpha builds connections list --project=[PROJECT_ID]

# If you don't have a connection yet, create one (interactive process)
# gcloud alpha builds connections create github [CONNECTION_NAME] --project=[PROJECT_ID]

# Create the trigger using an existing connection
gcloud builds triggers create github \
  --name=stylize-mcp-server-deploy \
  --repo=https://github.com/[YOUR_GITHUB_USERNAME_OR_ORG]/stylize-mcp-server \
  --branch-pattern=^main$ \
  --build-config=cloudbuild.yaml \
  --repo-type=GITHUB \
  --substitutions=_REGION=us-central1,_ARTIFACT_REPO_NAME=stylize-repo,_SERVICE_NAME=stylize-mcp-server,_OPENAI_API_KEY_SECRET_PATH=projects/[PROJECT_ID]/secrets/OPENAI_API_KEY/versions/latest \
  --project=[PROJECT_ID]

# Alternatively, if using a GitHub connection
# gcloud builds triggers create github \
#   --name=stylize-mcp-server-deploy \
#   --connection=[CONNECTION_NAME] \
#   --repository=[REPOSITORY_NAME] \
#   --branch-pattern=^main$ \
#   --build-config=cloudbuild.yaml \
#   --substitutions=_REGION=us-central1,_ARTIFACT_REPO_NAME=stylize-repo,_SERVICE_NAME=stylize-mcp-server,_OPENAI_API_KEY_SECRET_PATH=projects/[PROJECT_ID]/secrets/OPENAI_API_KEY/versions/latest \
#   --project=[PROJECT_ID]
```

Replace the following placeholders:
- `[PROJECT_ID]`: Your GCP project ID (e.g., `stylize-mcp-server`)
- `[YOUR_GITHUB_USERNAME_OR_ORG]`: Your GitHub username or organization name
- `[CONNECTION_NAME]`: Name of your Cloud Build GitHub connection (if using that flow)
- `[REPOSITORY_NAME]`: Name of your repository in the GitHub connection (if using that flow)

> **Note**: Using the CLI approach enables full automation of the CI/CD setup process and can be included in infrastructure scripts.

### 4. Grant IAM Permissions to Cloud Build Service Account

The Cloud Build service account needs specific permissions to deploy to Cloud Run. Run the following commands to grant these permissions programmatically:

```bash
# Get the Cloud Build service account email
CLOUD_BUILD_SA="$(gcloud projects describe [PROJECT_ID] --format='value(projectNumber)')@cloudbuild.gserviceaccount.com"

# Grant Cloud Run Admin role
gcloud projects add-iam-policy-binding [PROJECT_ID] \
  --member="serviceAccount:${CLOUD_BUILD_SA}" \
  --role="roles/run.admin"

# Grant Artifact Registry Writer role
gcloud projects add-iam-policy-binding [PROJECT_ID] \
  --member="serviceAccount:${CLOUD_BUILD_SA}" \
  --role="roles/artifactregistry.writer"

# Grant Service Account User role (to act as the stylize-mcp-sa)
gcloud projects add-iam-policy-binding [PROJECT_ID] \
  --member="serviceAccount:${CLOUD_BUILD_SA}" \
  --role="roles/iam.serviceAccountUser"

# Grant Secret Manager Secret Accessor role (to access the OPENAI_API_KEY)
gcloud projects add-iam-policy-binding [PROJECT_ID] \
  --member="serviceAccount:${CLOUD_BUILD_SA}" \
  --role="roles/secretmanager.secretAccessor"
```

Replace `[PROJECT_ID]` with your GCP Project ID (e.g., `stylize-mcp-server`).

> **Note**: These commands can be run directly by the human operator to programmatically grant all the necessary permissions to the Cloud Build service account.

## Verifying the Setup

To verify the CI/CD pipeline setup:

1. Make a change to the repository and push it to the `main` branch
2. Go to the Cloud Build section in the Google Cloud Console and check the build history
3. Ensure that the build completes successfully and the application is deployed to Cloud Run

## Troubleshooting

### Common Issues

1. **Build Failure**: Check the build logs for specific error messages
2. **Deployment Failure**: Ensure the Cloud Build service account has the necessary permissions
3. **Environment Variable Issues**: Verify that the substitution variables are correctly set in the trigger configuration

### Logs and Debugging

- Cloud Build logs: Available in the Cloud Build section of the Google Cloud Console
- Cloud Run logs: Available in the Cloud Run section of the Google Cloud Console
- Container logs: Can be viewed in the Cloud Logging section
