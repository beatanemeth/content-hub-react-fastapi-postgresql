# Shared by every test file. Each apply test applies the whole module, and the
# provider checks the IAM member format before any call; a random value fails.
mock_resource "google_service_account" {
  defaults = {
    member = "serviceAccount:content-hub-app@content-hub-sim.iam.gserviceaccount.com"
  }
}
