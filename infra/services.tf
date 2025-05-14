# Cloud Run service for the Stylize MCP Server

resource "google_cloud_run_v2_service" "stylize_mcp_server" {
  name     = "stylize-mcp-server"
  location = var.gcp_region
  
  # Ensure the Cloud Run API is enabled before creating the service
  depends_on = [google_project_service.run_api]

  template {
    containers {
      image = "us-docker.pkg.dev/cloudrun/container/hello" # Initial placeholder image

      ports {
        container_port = 8080
      }

      env {
        name  = "GCP_PROJECT_ID"
        value = var.gcp_project_id
      }

      # Redis env variables commented out to reduce costs during development
      # env {
      #   name  = "REDIS_HOST"
      #   value = google_redis_instance.stylize_mcp_redis.host
      # }

      # env {
      #   name  = "REDIS_PORT"
      #   value = google_redis_instance.stylize_mcp_redis.port
      # }

      env {
        name  = "OPENAI_API_KEY_SECRET_PATH"
        value = "projects/${var.gcp_project_id}/secrets/OPENAI_API_KEY/versions/latest"
      }
    }

    service_account = google_service_account.stylize_mcp_sa.email

    # VPC access commented out to reduce costs during development
    # vpc_access {
    #   connector = google_vpc_access_connector.stylize_mcp_vpc_connector.id
    #   egress    = "PRIVATE_RANGES_ONLY"
    # }
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }

  ingress = "INGRESS_TRAFFIC_ALL"

  # Lifecycle block to ignore container image changes managed by Cloud Build
  lifecycle {
    ignore_changes = [template.0.containers.0.image]
  }
}

# IAM binding for Cloud Run service (public access for MVP)
resource "google_cloud_run_service_iam_member" "stylize_mcp_server_public" {
  location = google_cloud_run_v2_service.stylize_mcp_server.location
  service  = google_cloud_run_v2_service.stylize_mcp_server.name
  role     = "roles/run.invoker"
  member   = "allUsers" # Public access for MVP
}
