# Shared by every test file. Each apply test applies the whole module, and the
# provider checks the IAM member format before any call; a random value fails.
# The email matches the member, so Cloud Run's service_account can be checked.
mock_resource "google_service_account" {
  defaults = {
    email  = "content-hub-app@content-hub-sim.iam.gserviceaccount.com"
    member = "serviceAccount:content-hub-app@content-hub-sim.iam.gserviceaccount.com"
  }
}
