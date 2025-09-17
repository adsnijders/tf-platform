# ---------------------------
# Terraform: Config
# ---------------------------
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

resource "google_sql_user" "user" {
  name      = var.db_username
  instance  = google_sql_database_instance.instance.name
  password  = var.db_password
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

      env {
        name  = "POSTGRES_NAME"
        value = google_sql_database.database.name
      }
      
      env {
        name  = "POSTGRES_USER"
        value = google_sql_user.user.name
      }

      env {
        name  = "POSTGRES_PASSWORD"
        value = google_sql_user.user.password
      }            

      env {
        name  = "INSTANCE_CONNECTION_NAME"
        value = google_sql_database_instance.instance.connection_name
      }

      # Mount
      volume_mounts {
        name = "cloudsql"
        mount_path = "/cloudsql"
      }
    }

    # Enable Cloud SQL Auth Proxy
    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.instance.connection_name]
      }
    }
  }
}

# ---------------------------
# Resource: iam binding
# ---------------------------
resource "google_cloud_run_service_iam_binding" "binding" {
  location  = google_cloud_run_v2_service.api_service.location
  project   = var.project_id
  service   = google_cloud_run_v2_service.api_service.name
  role      = "roles/run.invoker"
  members   = [
    "user:asnijders@xccelerated.io",
    "user:gclark@xccelerated.io"
  ]
}

# ---------------------------
# Resource: iam member
# ---------------------------
resource "google_cloud_run_service_iam_member" "public" {
  location  = google_cloud_run_v2_service.api_service.location
  project   = var.project_id
  service   = google_cloud_run_v2_service.api_service.name
  role      = "roles/run.invoker"
  member    = "allUsers"
}