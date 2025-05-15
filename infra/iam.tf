# iam.tf - Defines the Service Account and IAM bindings for the Stylize MCP Server

# Service Account for the Stylize MCP application
resource "google_service_account" "stylize_mcp_sa" {
  account_id   = "stylize-mcp-sa"
  display_name = "Stylize MCP Service Account"
  description  = "Service account for the Stylize MCP application with specific permissions following least privilege principle"
}

# IAM role bindings for the Stylize MCP service account
# Following principle of least privilege by assigning only the specific roles needed

# Storage Object Admin role for managing GCS buckets and objects
resource "google_project_iam_member" "stylize_mcp_storage_admin" {
  project = var.gcp_project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.stylize_mcp_sa.email}"
}

# Datastore User role for Firestore access
resource "google_project_iam_member" "stylize_mcp_datastore_user" {
  project = var.gcp_project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.stylize_mcp_sa.email}"
}

# AI Platform User role for Vision API access
resource "google_project_iam_member" "stylize_mcp_vision_user" {
  project = var.gcp_project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.stylize_mcp_sa.email}"
}

# Pub/Sub Publisher role for publishing to topics like stylize-analytics
resource "google_project_iam_member" "stylize_mcp_pubsub_publisher" {
  project = var.gcp_project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.stylize_mcp_sa.email}"
}

# Secret Manager Secret Accessor role for accessing API keys and other secrets
resource "google_project_iam_member" "stylize_mcp_secret_accessor" {
  project = var.gcp_project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.stylize_mcp_sa.email}"
}

resource "google_service_account_iam_member" "stylize_mcp_sa_actas_self" {
  service_account_id = google_service_account.stylize_mcp_sa.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.stylize_mcp_sa.email}"
}