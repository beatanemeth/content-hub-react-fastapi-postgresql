# The same region as Cloud Run, so pulling the image at start-up stays in the region.
resource "google_artifact_registry_repository" "app" {
  project       = var.project_id
  location      = var.region
  repository_id = "content-hub"
  description   = "Docker images of the content-hub app"
  format        = "DOCKER"
}
