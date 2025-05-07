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

output "vpc_connector_id" {
  description = "The ID of the Serverless VPC Access Connector"
  value       = google_vpc_access_connector.stylize_mcp_vpc_connector.id
}

output "vpc_connector_name" {
  description = "The name of the Serverless VPC Access Connector"
  value       = google_vpc_access_connector.stylize_mcp_vpc_connector.name
}

output "subnet_name" {
  description = "The name of the VPC connector subnet"
  value       = google_compute_subnetwork.stylize_mcp_vpc_connector_subnet.name
}

# Example output that might be added in future tasks:
# output "cloud_run_service_url" {
#   description = "The URL of the deployed Cloud Run service"
#   value       = google_cloud_run_service.stylize_mcp_service.status[0].url
# }
