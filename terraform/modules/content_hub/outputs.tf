output "registry_uri" {
  description = "Address of the Docker repository, the prefix of the image name for docker push."
  value       = google_artifact_registry_repository.app.registry_uri
}
