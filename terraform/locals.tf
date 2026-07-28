locals {

  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    Owner       = "Apurv"
    ManagedBy   = "Terraform"
  }

  instance_name = "${var.project_name}-server"

}