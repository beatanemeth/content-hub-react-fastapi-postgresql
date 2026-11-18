# No defaults: a missing value stops plan instead of building in the wrong project.
variable "project_id" {
  type        = string
  description = "ID of the GCP project that Part A provides; every resource is created in it."
}

variable "region" {
  type        = string
  description = "GCP region for every regional resource, for example europe-west1."
}
