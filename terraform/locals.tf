locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    Owner       = "Apurv"
    ManagedBy   = "Terraform"
  }

  tags = local.common_tags

  access_entries = {}

  cluster_name = var.cluster_name
}