mock_provider "google" {
  source = "./tests/mocks"
}

# GCP computes these; fixed values let the test check the image address and the socket volume.
override_resource {
  target = google_artifact_registry_repository.app
  values = { registry_uri = "europe-west1-docker.pkg.dev/content-hub-sim/content-hub" }
}

override_resource {
  target = google_sql_database_instance.main
  values = { connection_name = "content-hub-sim:europe-west1:content-hub-db-mock" }
}

# Simulated values: the Part A project and region, and an image tag.
variables {
  image_tag  = "abc1234"
  project_id = "content-hub-sim"
  region     = "europe-west1"
}

run "cloud_run_service" {
  command = apply

  assert {
    condition = (
      google_cloud_run_v2_service.app.template[0].containers[0].image ==
      "europe-west1-docker.pkg.dev/content-hub-sim/content-hub/content-hub:abc1234"
    )
    error_message = "Cloud Run must run the content-hub image with the given tag from this project's registry."
  }

  assert {
    condition = (
      google_cloud_run_v2_service.app.template[0].service_account ==
      "content-hub-app@content-hub-sim.iam.gserviceaccount.com"
    )
    error_message = "The service must run as the content-hub-app account, which holds the two grants."
  }

  assert {
    condition     = google_cloud_run_v2_service.app.template[0].scaling[0].max_instance_count == 1
    error_message = "One instance only: the mock sessions live in one process's memory."
  }

  assert {
    condition     = google_cloud_run_v2_service.app.deletion_protection == false
    error_message = "terraform destroy must be able to delete the service."
  }

  # The socket volume and its mount must meet at /cloudsql, the folder in DATABASE_URL.
  assert {
    condition = (
      google_cloud_run_v2_service.app.template[0].volumes[0].cloud_sql_instance[0].instances ==
      toset(["content-hub-sim:europe-west1:content-hub-db-mock"]) &&
      google_cloud_run_v2_service.app.template[0].containers[0].volume_mounts[0].name ==
      google_cloud_run_v2_service.app.template[0].volumes[0].name &&
      google_cloud_run_v2_service.app.template[0].containers[0].volume_mounts[0].mount_path == "/cloudsql"
    )
    error_message = "The Cloud SQL volume must hold this instance and be mounted on /cloudsql."
  }

  # env is a set, so the entry is picked by its name; the ref is [secret, version].
  assert {
    condition = one([
      for e in google_cloud_run_v2_service.app.template[0].containers[0].env :
      [e.value_source[0].secret_key_ref[0].secret, e.value_source[0].secret_key_ref[0].version]
      if e.name == "DATABASE_URL"
      ]) == [
      google_secret_manager_secret.database_url.secret_id,
      google_secret_manager_secret_version.database_url.version,
    ]
    error_message = "DATABASE_URL must come from the exact version of the content-hub secret."
  }

  assert {
    condition = (
      google_cloud_run_v2_service_iam_member.public.name == google_cloud_run_v2_service.app.name &&
      google_cloud_run_v2_service_iam_member.public.role == "roles/run.invoker" &&
      google_cloud_run_v2_service_iam_member.public.member == "allUsers"
    )
    error_message = "Anyone may call this service, and no other one."
  }

  assert {
    condition     = output.service_url == google_cloud_run_v2_service.app.uri
    error_message = "The service_url output must be the address of the service."
  }
}
