variable "gcp_project_id" {
  type        = string
  description = "The GCP project ID."
}

variable "gcp_region" {
  type        = string
  description = "The GCP region for resources."
  default     = "us-central1"
}

variable "gcp_zone" {
  type        = string
  description = "The GCP zone for resources."
  default     = "us-central1-a"
}
