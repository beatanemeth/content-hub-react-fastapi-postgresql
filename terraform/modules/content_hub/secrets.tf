resource "google_secret_manager_secret" "database_url" {
  project   = var.project_id
  secret_id = "content-hub-database-url"

  replication {
    auto {}
  }
}

# The host is the folder of the Cloud SQL Unix socket that Cloud Run mounts on
# /cloudsql; asyncpg reads it from the host query parameter.
resource "google_secret_manager_secret_version" "database_url" {
  secret = google_secret_manager_secret.database_url.id
  secret_data = format(
    "postgresql://%s:%s@/%s?host=/cloudsql/%s",
    google_sql_user.app.name,
    random_password.db_user.result,
    google_sql_database.app.name,
    google_sql_database_instance.main.connection_name,
  )
}
