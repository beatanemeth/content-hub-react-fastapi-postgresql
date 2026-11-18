variable "project_id" {
  type        = string
  description = "ID of the GCP project that Part A provides; set it in terraform.tfvars."
}

# The region default lives here, not in the module: this environment chooses it.
variable "region" {
  type        = string
  description = "GCP region for every regional resource."
  default     = "europe-west1"
}
