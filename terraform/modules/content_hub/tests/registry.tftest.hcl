mock_provider "google" {}

# Simulated values: the Part A project and region, and an image tag.
variables {
  image_tag  = "abc1234"
  project_id = "content-hub-sim"
  region     = "europe-west1"
}

run "registry" {
  command = plan

  assert {
    condition = (
      google_artifact_registry_repository.app.repository_id == "content-hub" &&
      google_artifact_registry_repository.app.format == "DOCKER" &&
      google_artifact_registry_repository.app.location == "europe-west1"
    )
    error_message = "A Docker repository in the same region as Cloud Run."
  }
}

# apply, because registry_uri is computed: at plan it is still unknown.
run "outputs" {
  command = apply

  assert {
    condition     = output.registry_uri == google_artifact_registry_repository.app.registry_uri
    error_message = "registry_uri must come from the repository's registry_uri attribute."
  }
}
