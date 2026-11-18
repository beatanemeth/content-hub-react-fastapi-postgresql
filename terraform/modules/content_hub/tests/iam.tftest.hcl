mock_provider "google" {
  # The provider checks the IAM member format before any call; a random mock
  # value fails.
  mock_resource "google_service_account" {
    defaults = {
      member = "serviceAccount:content-hub-app@content-hub-sim.iam.gserviceaccount.com"
    }
  }
}

# Simulated values: the Part A project and region, and an image tag.
variables {
  project_id = "content-hub-sim"
  region     = "europe-west1"
  image_tag  = "abc1234"
}

run "service_account_and_grants" {
  command = apply

  assert {
    condition     = google_service_account.app.account_id == "content-hub-app"
    error_message = "Cloud Run runs as the content-hub-app service account."
  }

  # Cloud SQL has no grants per instance, so this one role is on the project.
  assert {
    condition = (
      google_project_iam_member.app_cloudsql_client.project == "content-hub-sim" &&
      google_project_iam_member.app_cloudsql_client.role == "roles/cloudsql.client" &&
      google_project_iam_member.app_cloudsql_client.member == google_service_account.app.member
    )
    error_message = "The app account needs cloudsql.client on the project."
  }

  assert {
    condition = (
      google_secret_manager_secret_iam_member.app_database_url.secret_id == google_secret_manager_secret.database_url.secret_id &&
      google_secret_manager_secret_iam_member.app_database_url.role == "roles/secretmanager.secretAccessor" &&
      google_secret_manager_secret_iam_member.app_database_url.member == google_service_account.app.member
    )
    error_message = "The app account needs secretAccessor on the DATABASE_URL secret only."
  }
}
