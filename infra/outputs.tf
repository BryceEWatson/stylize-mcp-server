# This file contains outputs from the Terraform configuration.
# These outputs can be used by subsequent tasks or for reference.

# Networking outputs
output "vpc_network_id" {
  description = "The ID of the VPC network"
  value       = google_compute_network.stylize_mcp_vpc.id
}

output "vpc_network_name" {
  description = "The name of the VPC network"
  value       = google_compute_network.stylize_mcp_vpc.name
}

# VPC Connector outputs commented out to reduce costs during development
# output "vpc_connector_id" {
#   description = "The ID of the Serverless VPC Access Connector"
#   value       = google_vpc_access_connector.stylize_mcp_vpc_connector.id
# }

# output "vpc_connector_name" {
#   description = "The name of the Serverless VPC Access Connector"
#   value       = google_vpc_access_connector.stylize_mcp_vpc_connector.name
# }

output "subnet_name" {
  description = "The name of the VPC connector subnet"
  value       = google_compute_subnetwork.stylize_mcp_vpc_connector_subnet.name
}

# Service account outputs
output "service_account_email" {
  description = "The email address of the Stylize MCP service account"
  value       = google_service_account.stylize_mcp_sa.email
}

output "service_account_id" {
  description = "The ID of the Stylize MCP service account"
  value       = google_service_account.stylize_mcp_sa.id
}

output "service_account_name" {
  description = "The fully-qualified name of the Stylize MCP service account"
  value       = google_service_account.stylize_mcp_sa.name
}

# Storage outputs
output "originals_bucket_name" {
  description = "The name of the GCS bucket for original images"
  value       = google_storage_bucket.stylize_originals_bucket.name
}

output "originals_bucket_url" {
  description = "The URL of the GCS bucket for original images"
  value       = google_storage_bucket.stylize_originals_bucket.url
}

output "variants_bucket_name" {
  description = "The name of the GCS bucket for stylized/variant images"
  value       = google_storage_bucket.stylize_variants_bucket.name
}

output "variants_bucket_url" {
  description = "The URL of the GCS bucket for stylized/variant images"
  value       = google_storage_bucket.stylize_variants_bucket.url
}

# Redis outputs
# Redis outputs commented out to reduce costs during development
# output "redis_host" {
#   description = "The hostname or IP address of the Redis instance"
#   value       = google_redis_instance.stylize_mcp_redis.host
# }

# output "redis_port" {
#   description = "The port number of the Redis instance"
#   value       = google_redis_instance.stylize_mcp_redis.port
# }

# Pub/Sub outputs
output "analytics_topic_id" {
  description = "The ID of the Pub/Sub topic for analytics events"
  value       = google_pubsub_topic.stylize_analytics_topic.id
}

output "analytics_topic_name" {
  description = "The name of the Pub/Sub topic for analytics events"
  value       = google_pubsub_topic.stylize_analytics_topic.name
}

# Secret Manager outputs
output "openai_api_key_secret_id" {
  description = "The ID of the OpenAI API key secret"
  value       = google_secret_manager_secret.openai_api_key.id
}

output "openai_api_key_secret_name" {
  description = "The fully-qualified resource name of the OpenAI API key secret"
  value       = google_secret_manager_secret.openai_api_key.name
}

# Cloud Run outputs
output "cloud_run_service_url" {
  description = "The URL of the deployed Cloud Run service"
  value       = google_cloud_run_v2_service.stylize_mcp_server.uri
}
