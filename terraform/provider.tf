provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "Stockloom"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}