terraform {
    required_providers {
        google = {
            source  = "hashicorp/google"
            version = "6.8.0"
        }
    }
}

# ---------------------------
# Provider: Google
# ---------------------------
provider "google" {
    project = var.project_id
    region  = var.region
}

# ---------------------------
# Data source: Artifact Registry
# ---------------------------
data "google_artifact_registry_repository" "my_repo" {
    project         = var.project_id
    location        = var.region
    repository_id   = var.artifact_repo_id
}

# ---------------------------
# Resource: Cloud SQL (PostgreSQL example)
# ---------------------------
resource "google_sql_database" "database" {
  name     = "my-database"
  instance = google_sql_database_instance.instance.name
}

# See versions at https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/sql_database_instance#database_version
resource "google_sql_database_instance" "instance" {
  name             = "my-database-instance"
  region           = var.region
  database_version = "POSTGRES_15"
  settings {
    tier = "db-custom-1-3840"
  }

  deletion_protection = false
}

# ---------------------------
# Resource: Cloud Run Service V2
# ---------------------------
resource "google_cloud_run_v2_service" "api_service" {
  name                = "cloudrun-service"
  location            = var.region
  deletion_protection = false
  ingress             = "INGRESS_TRAFFIC_ALL"

  template {
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_repo_id}/${var.image_name}:latest"
    }
  }
}