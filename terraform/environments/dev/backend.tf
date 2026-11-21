# The bucket comes from backend.hcl (terraform init -backend-config=backend.hcl);
# the prefix keeps this state apart from the pipeline's.
terraform {
  backend "gcs" {
    prefix = "content-hub"
  }
}
