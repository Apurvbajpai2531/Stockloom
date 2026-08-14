variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-south-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "stockloom"
}

variable "vpc_cidr" {
  description = "VPC CIDR"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones for EKS"
  type        = list(string)

  default = [
    "ap-south-1a",
    "ap-south-1b"
  ]
}

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = "stockloom-eks"
}

variable "kubernetes_version" {
  description = "EKS Kubernetes version"
  type        = string
  default     = "1.33"
}

variable "node_instance_type" {
  description = "EKS worker node instance type"
  type        = string
  default     = "t3.small"
}

variable "node_min_size" {
  description = "Minimum number of worker nodes"
  type        = number
  default     = 2
}

variable "node_max_size" {
  description = "Maximum number of worker nodes"
  type        = number
  default     = 3
}

variable "node_desired_size" {
  description = "Desired number of worker nodes"
  type        = number
  default     = 3
}

variable "node_disk_size" {
  description = "Worker node root disk size in GB"
  type        = number
  default     = 20
}

variable "enable_argocd" {
  description = "Enable ArgoCD installation"
  type        = bool
  default     = true
}

variable "argocd_chart_version" {
  description = "ArgoCD Helm chart version"
  type        = string
  default     = "7.9.0"
}
