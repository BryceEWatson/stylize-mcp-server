# apis_secrets.tf - Enables necessary Google Cloud APIs and configures Secret Manager

# Enable required Google Cloud APIs
# Setting disable_on_destroy = false prevents accidental disabling if the Terraform configuration is destroyed

# Cloud Run API
resource "google_project_service" "run_api" {
  project                    = var.gcp_project_id
  service                    = "run.googleapis.com"
  disable_dependent_services = false
  disable_on_destroy         = false
}

# Cloud Build API
resource "google_project_service" "cloudbuild_api" {
  project                    = var.gcp_project_id
  service                    = "cloudbuild.googleapis.com"
  disable_dependent_services = false
  disable_on_destroy         = false
}

# Cloud Firestore API
resource "google_project_service" "firestore_api" {
  project                    = var.gcp_project_id
  service                    = "firestore.googleapis.com"
  disable_dependent_services = false
  disable_on_destroy         = false
}

# Cloud Vision API
resource "google_project_service" "vision_api" {
  project                    = var.gcp_project_id
  service                    = "vision.googleapis.com"
  disable_dependent_services = false
  disable_on_destroy         = false
}

# Memorystore for Redis API
resource "google_project_service" "redis_api" {
  project                    = var.gcp_project_id
  service                    = "redis.googleapis.com"
  disable_dependent_services = false
  disable_on_destroy         = false
}

# Serverless VPC Access API
resource "google_project_service" "vpcaccess_api" {
  project                    = var.gcp_project_id
  service                    = "vpcaccess.googleapis.com"
  disable_dependent_services = false
  disable_on_destroy         = false
}

# Secret Manager API
resource "google_project_service" "secretmanager_api" {
  project                    = var.gcp_project_id
  service                    = "secretmanager.googleapis.com"
  disable_dependent_services = false
  disable_on_destroy         = false
}

# Cloud Pub/Sub API
resource "google_project_service" "pubsub_api" {
  project                    = var.gcp_project_id
  service                    = "pubsub.googleapis.com"
  disable_dependent_services = false
  disable_on_destroy         = false
}

# Artifact Registry API
resource "google_project_service" "artifactregistry_api" {
  project                    = var.gcp_project_id
  service                    = "artifactregistry.googleapis.com"
  disable_dependent_services = false
  disable_on_destroy         = false
}

# Secret Manager configuration for OpenAI API key

# Create the secret
resource "google_secret_manager_secret" "openai_api_key" {
  secret_id = "OPENAI_API_KEY"

  # Ensure the Secret Manager API is enabled before creating secrets
  depends_on = [google_project_service.secretmanager_api]

  replication {
    auto {
      # Automatic replication provides the highest availability
    }
  }
}

# Create an initial version with a placeholder value
# IMPORTANT: The actual API key will be added manually after deployment
resource "google_secret_manager_secret_version" "openai_api_key_version" {
  secret         = google_secret_manager_secret.openai_api_key.id
  secret_data_wo = "dummy-openai-api-key-placeholder"
  enabled        = true
}
