terraform {
  backend "s3" {
    bucket  = "sensor-backend-terraform-state"
    key     = "prod/terraform.tfstate"
    region  = "us-east-2"
    encrypt = true
    # Removed dynamodb_table - no more lock issues
  }
}
