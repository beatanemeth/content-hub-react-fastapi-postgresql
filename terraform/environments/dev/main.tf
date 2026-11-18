provider "google" {
  project = var.project_id
  region  = var.region
}

module "content_hub" {
  source = "../../modules/content_hub"

  project_id = var.project_id
  region     = var.region
}
