mock_provider "google" {
  # The test applies the whole module, and the provider checks the IAM member
  # format before any call; a random mock value fails.
  mock_resource "google_service_account" {
    defaults = {
      member = "serviceAccount:mock@content-hub-sim.iam.gserviceaccount.com"
    }
  }
}

# Simulated values: the Part A project and region, and an image tag.
variables {
  project_id = "content-hub-sim"
  region     = "europe-west1"
  image_tag  = "abc1234"
}

run "registry_and_outputs" {
  command = apply

  assert {
    condition = (
      google_artifact_registry_repository.app.repository_id == "content-hub" &&
      google_artifact_registry_repository.app.format == "DOCKER" &&
      google_artifact_registry_repository.app.location == "europe-west1"
    )
    error_message = "A Docker repository in the same region as Cloud Run."
  }

  # docker push (Phase 5) and the Auth Proxy (Phase 6) read these outputs;
  # a swapped value would send them to the wrong place.
  assert {
    condition = (
      output.registry_uri == google_artifact_registry_repository.app.registry_uri &&
      output.sql_connection_name == google_sql_database_instance.main.connection_name &&
      output.service_account_email == google_service_account.app.email
    )
    error_message = "Each output must come from its own resource."
  }
}
