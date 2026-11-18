# The identity of the Cloud Run service: it holds only the two roles below.
resource "google_service_account" "app" {
  project      = var.project_id
  account_id   = "content-hub-app"
  display_name = "content-hub Cloud Run service"
}

# Cloud SQL grants this role on the project only; it lets the account open
# the connector tunnel, while the database user and password still apply.
resource "google_project_iam_member" "app_cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = google_service_account.app.member
}

# On the one secret, not the project: the account cannot read other secrets.
resource "google_secret_manager_secret_iam_member" "app_database_url" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.database_url.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = google_service_account.app.member
}
