# A module's outputs stay inside the caller; these lines pass them on to
# terraform apply and terraform output.
output "registry_uri" {
  description = "Address of the Docker repository, the prefix of the image name for docker push."
  value       = module.content_hub.registry_uri
}
