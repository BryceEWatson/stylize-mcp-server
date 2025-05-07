terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0.0"
    }
  }

  # Uncomment this block to configure a GCS backend for state management
  # backend "gcs" {
  #   bucket = "stylize-mcp-terraform-state"
  #   prefix = "terraform/state"
  # }
}
