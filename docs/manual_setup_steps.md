# Manual Setup Steps for Stylize MCP Server

This document outlines steps that must be performed manually after Terraform infrastructure provisioning.

## Setting the OpenAI API Key in Secret Manager

### Background
For security reasons, the actual OpenAI API key is not stored in the Terraform code or Git repository. After Terraform creates the Secret Manager resource with a placeholder value, you must manually update it with the actual API key.

### Steps to Add the OpenAI API Key

1. **Wait for Terraform to Complete**: Run `terraform apply` from the `infra` directory first. This will create the Secret Manager resource with a placeholder value.

2. **Access the GCP Console**:
   - Go to [GCP Console](https://console.cloud.google.com/)
   - Ensure you're in the correct project (`stylize-mcp` or your project ID)
   - Navigate to "Security" → "Secret Manager"

3. **Update the Secret**:
   - Find the secret named `OPENAI_API_KEY`
   - Click on the secret name to open its details
   - Click "Add New Version"
   - Paste your actual OpenAI API key into the "Secret value" field
   - Click "Create"

4. **Verify the Secret Version**:
   - Ensure the new version is marked as "Enabled"
   - Note the version number for reference (typically should be version 2 if this is your first update after Terraform)

### Alternative: Using gcloud CLI

You can also update the secret using the Google Cloud CLI:

```bash
echo -n "your-actual-openai-api-key" | gcloud secrets versions add OPENAI_API_KEY --data-file=-
```

### Important Security Notes

- **Never commit the actual API key to Git or include it in Terraform code**
- Consider implementing key rotation policies for production
- Ensure only authorized personnel have access to view/manage this secret
- The service account (`stylize-mcp-sa`) has been granted the `roles/secretmanager.secretAccessor` role to access this secret

## Next Steps After Manual Setup

Once the OpenAI API key is properly configured in Secret Manager, you can proceed with deploying the application code to Cloud Run, which will be configured to access this secret.
