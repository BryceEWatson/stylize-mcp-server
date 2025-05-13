# storage.tf - Defines storage and database resources for the Stylize MCP Server

# GCS bucket for original images
resource "google_storage_bucket" "stylize_originals_bucket" {
  name                        = "stylize-originals-${var.gcp_project_id}"
  location                    = var.gcp_region
  uniform_bucket_level_access = true
  force_destroy               = false # Prevents accidental deletion of bucket and its contents

  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD", "PUT", "POST"]
    response_header = ["*"]
    max_age_seconds = 3600
  }

  lifecycle_rule {
    condition {
      age = 60 # 60 days retention for original images
    }
    action {
      type = "Delete"
    }
  }
}

# GCS bucket for stylized/variant images
resource "google_storage_bucket" "stylize_variants_bucket" {
  name                        = "stylize-variants-${var.gcp_project_id}"
  location                    = var.gcp_region
  uniform_bucket_level_access = true
  force_destroy               = false # Prevents accidental deletion of bucket and its contents

  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD", "PUT", "POST"]
    response_header = ["*"]
    max_age_seconds = 3600
  }

  lifecycle_rule {
    condition {
      age = 30 # 30 days retention for variant images
    }
    action {
      type = "Delete"
    }
  }
}

# Memorystore for Redis instance (for caching and rate limiting)
resource "google_redis_instance" "stylize_mcp_redis" {
  name           = "stylize-mcp-redis"
  tier           = "BASIC"
  memory_size_gb = 1
  region         = var.gcp_region

  # Connect to the VPC created in network.tf
  authorized_network = google_compute_network.stylize_mcp_vpc.id

  redis_version = "REDIS_6_X"
  display_name  = "Stylize MCP Redis Cache"
  redis_configs = {
    maxmemory-policy = "allkeys-lru" # Least recently used eviction policy
  }
}

# Pub/Sub topic for analytics events
resource "google_pubsub_topic" "stylize_analytics_topic" {
  name = "stylize-analytics"

  # Setting a message retention duration (3 days)
  message_retention_duration = "259200s"

  # Enable message ordering if analytics events order matters
  message_storage_policy {
    allowed_persistence_regions = [
      var.gcp_region,
    ]
  }
}
