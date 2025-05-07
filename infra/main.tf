provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
  zone    = var.gcp_zone
}

# This file will serve as the entry point for our Terraform configuration.
# Additional resources will be defined in separate .tf files for better organization,
# such as network.tf, storage.tf, iam.tf, etc. in subsequent tasks.
