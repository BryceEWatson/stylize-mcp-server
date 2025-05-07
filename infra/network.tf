# network.tf - Defines the core networking infrastructure for the Stylize MCP Server

# VPC Network for the Stylize MCP application
resource "google_compute_network" "stylize_mcp_vpc" {
  name                    = "stylize-mcp-vpc"
  auto_create_subnetworks = false
  description             = "VPC network for the Stylize MCP application"
}

# Subnet for the Serverless VPC Access Connector
resource "google_compute_subnetwork" "stylize_mcp_vpc_connector_subnet" {
  name          = "stylize-mcp-vpc-connector-subnet"
  ip_cidr_range = "10.8.0.0/28" # As suggested in the implementation plan
  region        = var.gcp_region
  network       = google_compute_network.stylize_mcp_vpc.id
  description   = "Subnet for the Serverless VPC Access Connector"
}

# Serverless VPC Access Connector for connecting Cloud Run to VPC resources
resource "google_vpc_access_connector" "stylize_mcp_vpc_connector" {
  name = "stylize-mcp-vpc-connector"
  subnet {
    name = google_compute_subnetwork.stylize_mcp_vpc_connector_subnet.name
  }
  region         = var.gcp_region
  max_throughput = 300        # Default value in Mbps
  min_throughput = 200        # Default value in Mbps
  machine_type   = "e2-micro" # Cost-effective option for MVP
}

# Cloud Router for NAT gateway
resource "google_compute_router" "stylize_mcp_router" {
  name        = "stylize-mcp-router"
  network     = google_compute_network.stylize_mcp_vpc.id
  region      = var.gcp_region
  description = "Router for Cloud NAT in the Stylize MCP VPC"
}

# Cloud NAT for allowing outbound traffic from private instances
resource "google_compute_router_nat" "stylize_mcp_nat" {
  name                               = "stylize-mcp-nat"
  router                             = google_compute_router.stylize_mcp_router.name
  region                             = var.gcp_region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "LIST_OF_SUBNETWORKS"

  subnetwork {
    name                    = google_compute_subnetwork.stylize_mcp_vpc_connector_subnet.id
    source_ip_ranges_to_nat = ["ALL_IP_RANGES"]
  }

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}
