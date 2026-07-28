variable "aws_region" {
  type    = string
  default = "ap-south-1"

}

variable "environment" {
  type    = string
  default = "dev"
}

variable "project_name" {
  type    = string
  default = "stockloom"
}

variable "vpc_cidr" {
  default = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  default = "10.0.1.0/24"
}

variable "availability_zone" {
  default = "ap-south-1a"
}

variable "instance_type" {
  default = "t3.micro"
}

variable "key_name" {
  default = "stockloom-key"
}

variable "public_key_path" {
  default = "~/.ssh/id_rsa.pub"
}