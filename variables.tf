variable "project_id" {
    type = string
    default = "ae-terraform-2025"
}

variable "region" { 
    type = string
    default = "europe-west4" 
}

variable "artifact_repo_id" {
    type = string
    default = "ae-2025-registry"
}

variable "image_name" {
    type = string
    default = "ad-image"
}

variable "db_username" {
    type = string
    default = "fastapi_db"
}

variable "db_password" {
    type = string
    sensitive = true
}