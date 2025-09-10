terraform {
    backend "gcs" {
        bucket = "terraform-state-ad"
        prefix = "terraform/state"
    }
}