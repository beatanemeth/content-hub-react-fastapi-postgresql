mock_provider "google" {
  # The test applies the whole module, and the provider checks the IAM member
  # format before any call; a random mock value fails.
  mock_resource "google_service_account" {
    defaults = {
      member = "serviceAccount:mock@content-hub-sim.iam.gserviceaccount.com"
    }
  }
}

# GCP computes the connection name; a fixed value lets the test check the whole URL.
override_resource {
  target = google_sql_database_instance.main
  values = { connection_name = "content-hub-sim:europe-west1:content-hub-db-mock" }
}

# Simulated Part A values.
variables {
  project_id = "content-hub-sim"
  region     = "europe-west1"
}

run "database_url_secret" {
  command = apply

  assert {
    condition     = google_secret_manager_secret.database_url.secret_id == "content-hub-database-url"
    error_message = "Cloud Run refers to the secret by this ID."
  }

  assert {
    condition     = google_secret_manager_secret_version.database_url.secret == google_secret_manager_secret.database_url.id
    error_message = "The version must belong to the DATABASE_URL secret."
  }

  # The Unix socket form: no host before the database, the socket folder in ?host=.
  assert {
    condition = google_secret_manager_secret_version.database_url.secret_data == format(
      "postgresql://content_hub:%s@/content_hub?host=/cloudsql/content-hub-sim:europe-west1:content-hub-db-mock",
      random_password.db_user.result,
    )
    error_message = "DATABASE_URL must use the app's user and database and the Cloud SQL socket folder."
  }
}
