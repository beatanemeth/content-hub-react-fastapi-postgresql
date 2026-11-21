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
