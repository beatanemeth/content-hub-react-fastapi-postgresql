# The google provider is fake: no GCP call, no cost. The random provider is
# real; it runs on the laptop only.
mock_provider "google" {}

# Simulated values: the Part A project and region, and an image tag.
variables {
  image_tag  = "abc1234"
  project_id = "content-hub-sim"
  region     = "europe-west1"
}

# apply, because the name suffix from random_id is only known after apply.
run "instance" {
  command = apply

  assert {
    condition = (
      google_sql_database_instance.main.database_version == "POSTGRES_18" &&
      google_sql_database_instance.main.settings[0].edition == "ENTERPRISE" &&
      google_sql_database_instance.main.settings[0].tier == "db-f1-micro"
    )
    error_message = "PostgreSQL 18 on the shared-core tier, which needs the ENTERPRISE edition."
  }

  assert {
    condition     = can(regex("^content-hub-db-[0-9a-f]{8}$", google_sql_database_instance.main.name))
    error_message = "The instance name needs the 8-character random suffix."
  }

  assert {
    condition     = google_sql_database_instance.main.deletion_protection == false
    error_message = "terraform destroy must be able to delete the instance."
  }

  assert {
    condition     = google_sql_database_instance.main.settings[0].backup_configuration[0].enabled == false
    error_message = "No backups: the seed data can be loaded again."
  }

  assert {
    condition = (
      google_sql_database_instance.main.settings[0].ip_configuration[0].ipv4_enabled &&
      length(google_sql_database_instance.main.settings[0].ip_configuration[0].authorized_networks) == 0
    )
    error_message = "Public IP for the connectors, with no network opened to the internet."
  }
}
