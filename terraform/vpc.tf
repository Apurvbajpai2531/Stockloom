module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 6.0"

  name = "${var.project_name}-vpc"
  cidr = var.vpc_cidr

  azs = var.availability_zones

  public_subnets = [
    "10.0.101.0/24",
    "10.0.102.0/24"
  ]

  private_subnets = [
    "10.0.1.0/24",
    "10.0.2.0/24"
  ]

  intra_subnets = [
    "10.0.201.0/24",
    "10.0.202.0/24"
  ]

  enable_nat_gateway = true
  single_nat_gateway = true

  enable_dns_hostnames = true
  enable_dns_support   = true

  public_subnet_tags = {
    "kubernetes.io/role/elb" = "1"
  }

  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = "1"
  }

  intra_subnet_tags = {
    "kubernetes.io/role/internal-elb" = "1"
  }

  tags = local.common_tags
}