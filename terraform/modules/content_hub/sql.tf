# Cloud SQL blocks a deleted instance's name for up to a week, so each
# destroy and apply cycle needs a new name.
resource "random_id" "db_suffix" {
  byte_length = 4
}

resource "google_sql_database_instance" "main" {
  project          = var.project_id
  region           = var.region
  name             = "content-hub-db-${random_id.db_suffix.hex}"
  database_version = "POSTGRES_18"

  # Without false, terraform destroy stops at this instance.
  deletion_protection = false

  settings {
    # PostgreSQL 16 and later default to ENTERPRISE_PLUS, which has no shared-core tier.
    edition = "ENTERPRISE"
    tier    = "db-f1-micro"

    disk_size = 10

    # The seed data can be loaded again, so no backup storage is paid for.
    backup_configuration {
      enabled = false
    }

    # Public IP with no authorised networks: only the Cloud SQL connectors
    # (Cloud Run, the Auth Proxy) can connect, through an IAM-checked tunnel.
    ip_configuration {
      ipv4_enabled = true
    }
  }
}

resource "google_sql_database" "app" {
  project  = var.project_id
  instance = google_sql_database_instance.main.name
  name     = "content_hub"
}

# No special characters: the password goes into DATABASE_URL without URL encoding.
resource "random_password" "db_user" {
  length  = 32
  special = false
}

resource "google_sql_user" "app" {
  project  = var.project_id
  instance = google_sql_database_instance.main.name
  name     = "content_hub"
  password = random_password.db_user.result

  # The user owns the tables after the seed, so PostgreSQL refuses to drop it.
  # ABANDON skips the drop; deleting the instance removes the user anyway.
  deletion_policy = "ABANDON"
}
