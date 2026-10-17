# Manual Setup Checklist for Stylize MCP Server

This checklist outlines the critical manual setup actions required after running `terraform apply` and before the CI/CD pipeline becomes fully operational. Check off each item as you complete it.

## Prerequisites

- [ ] Successful run of `terraform apply` from the `infra/` directory
- [ ] Access to the GCP project with appropriate permissions
- [ ] GitHub repository set up and code pushed

## Post-Terraform Manual Steps

### 1. Secret Management

#### Background
For security reasons, the actual OpenAI API key is not stored in the Terraform code or Git repository. Terraform creates the Secret Manager resource with a placeholder value, which you must manually update with your actual API key.

- [ ] Update the OpenAI API key in Secret Manager with the actual key:
  ```bash
  echo -n "YOUR_ACTUAL_OPENAI_API_KEY" | gcloud secrets versions add OPENAI_API_KEY --data-file=- --project=[PROJECT_ID]
  ```

#### Important Security Notes
- **Never commit the actual API key to Git or include it in Terraform code**
- Consider implementing key rotation policies for production environments
- Ensure only authorized personnel have access to view/manage this secret
- The service account (`stylize-mcp-sa`) has been granted the `roles/secretmanager.secretAccessor` role to access this secret

### 2. Artifact Registry Setup

- [ ] Create the Artifact Registry Docker repository (if not done via Terraform):
  ```bash
  gcloud artifacts repositories create stylize-repo \
    --repository-format=docker \
    --location=us-central1 \
    --description="Docker repository for Stylize MCP Server images" \
    --project=[PROJECT_ID]
  ```

### 3. Cloud Build GitHub Integration

- [ ] (One-time, if applicable) Establish Cloud Build connection to GitHub:
  ```bash
  gcloud alpha builds connections create github [CONNECTION_NAME] --project=[PROJECT_ID]
  ```

### 4. Cloud Build Service Account Permissions

- [ ] Grant required IAM permissions to the Cloud Build service account:
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

### 5. Cloud Build Trigger Configuration

- [ ] Create and configure the Cloud Build trigger:
  ```bash
  gcloud builds triggers create github \
    --name=stylize-mcp-server-deploy \
    --repo=https://github.com/[YOUR_GITHUB_USERNAME_OR_ORG]/stylize-mcp-server \
    --branch-pattern=^main$ \
    --build-config=cloudbuild.yaml \
    --repo-type=GITHUB \
    --substitutions=_REGION=us-central1,_ARTIFACT_REPO_NAME=stylize-repo,_SERVICE_NAME=stylize-mcp-server,_OPENAI_API_KEY_SECRET_PATH=projects/[PROJECT_ID]/secrets/OPENAI_API_KEY/versions/latest \
    --project=[PROJECT_ID]
  ```

### 6. Budget Alerts Configuration

- [ ] Set up billing budget alerts:
  ```bash
  gcloud beta billing budgets create \
    --billing-account=[BILLING_ACCOUNT_ID] \
    --display-name="Stylize MCP Server MVP Budget" \
    --budget-amount=20USD \
    --threshold-rules=percent=0.5,basis=current_spend \
    --threshold-rules=percent=0.9,basis=current_spend \
    --threshold-rules=percent=1.0,basis=current_spend \
    --email-recipients=[YOUR_EMAIL] \
    --projects=projects/[PROJECT_ID]
  ```

## Verification

- [ ] Verify successful Cloud Build setup by pushing a small change to the main branch
- [ ] Check Cloud Build history to ensure the build completes successfully
- [ ] Verify that the application is deployed to Cloud Run correctly
- [ ] Test the deployed application's functionality

## Notes

- Replace all placeholder values (`[PROJECT_ID]`, `[YOUR_GITHUB_USERNAME_OR_ORG]`, `[CONNECTION_NAME]`, `[BILLING_ACCOUNT_ID]`, `[YOUR_EMAIL]`) with your actual values.
- For detailed instructions on each step, refer to the documentation in the `docs/` directory.
- If any step fails, consult the troubleshooting sections in the relevant documentation files.
