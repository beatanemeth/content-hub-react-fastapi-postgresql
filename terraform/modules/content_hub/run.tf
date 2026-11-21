resource "google_cloud_run_v2_service" "app" {
  project  = var.project_id
  location = var.region
  name     = "content-hub"
  ingress  = "INGRESS_TRAFFIC_ALL"

  # The provider defaults to true, which would stop terraform destroy here.
  deletion_protection = false

  template {
    service_account = google_service_account.app.email

    # The mock sessions live in one process's memory, so one instance only.
    scaling {
      max_instance_count = 1
    }

    # Cloud Run runs the Cloud SQL connector and puts its Unix socket in this volume.
    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.main.connection_name]
      }
    }

    containers {
      image = "${google_artifact_registry_repository.app.registry_uri}/content-hub:${var.image_tag}"

      ports {
        container_port = 8080
      }

      # The exact version, not "latest": a new secret version starts a new revision.
      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.database_url.secret_id
            version = google_secret_manager_secret_version.database_url.version
          }
        }
      }

      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }
    }
  }

  # The first revision starts during apply and fails without these two grants.
  depends_on = [
    google_project_iam_member.app_cloudsql_client,
    google_secret_manager_secret_iam_member.app_database_url,
  ]
}

# Anyone on the internet may call the service: it is a public website. Writing
# still needs the mock session cookie.
resource "google_cloud_run_v2_service_iam_member" "public" {
  project  = google_cloud_run_v2_service.app.project
  location = google_cloud_run_v2_service.app.location
  name     = google_cloud_run_v2_service.app.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
