# A module's outputs stay inside the caller; these lines pass them on to
# terraform apply and terraform output.
output "registry_uri" {
  description = "Address of the Docker repository, the prefix of the image name for docker push."
  value       = module.content_hub.registry_uri
}

output "service_url" {
  description = "HTTPS address of the Cloud Run service, where the app answers."
  value       = module.content_hub.service_url
}

output "sql_connection_name" {
  description = "Connection name of the Cloud SQL instance (project:region:instance) for the Auth Proxy."
  value       = module.content_hub.sql_connection_name
}
