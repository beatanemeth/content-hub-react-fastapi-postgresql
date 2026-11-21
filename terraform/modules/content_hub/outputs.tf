output "registry_uri" {
  description = "Address of the Docker repository, the prefix of the image name for docker push."
  value       = google_artifact_registry_repository.app.registry_uri
}

output "service_url" {
  description = "HTTPS address of the Cloud Run service, where the app answers."
  value       = google_cloud_run_v2_service.app.uri
}

output "sql_connection_name" {
  description = "Connection name of the Cloud SQL instance (project:region:instance) for the Auth Proxy."
  value       = google_sql_database_instance.main.connection_name
}
