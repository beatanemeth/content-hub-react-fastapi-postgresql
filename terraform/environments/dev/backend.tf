# A backend block cannot read variables, so the bucket (Part A's state bucket)
# comes from backend.hcl: terraform init -backend-config=backend.hcl.
# The prefix keeps this state apart from the pipeline's "content-pipeline" state.
terraform {
  backend "gcs" {
    prefix = "content-hub"
  }
}
