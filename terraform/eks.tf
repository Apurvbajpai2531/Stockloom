data "aws_iam_policy_document" "ebs_csi_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["pods.eks.amazonaws.com"]
    }

    actions = [
      "sts:AssumeRole",
      "sts:TagSession"
    ]
  }
}

resource "aws_iam_role" "ebs_csi" {
  name = "${var.cluster_name}-ebs-csi-role"

  assume_role_policy = data.aws_iam_policy_document.ebs_csi_assume_role.json

  tags = local.tags
}

resource "aws_iam_role_policy_attachment" "ebs_csi" {
  role = aws_iam_role.ebs_csi.name

  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy"
}

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 21.0"

  name               = var.cluster_name
  kubernetes_version = var.kubernetes_version

  endpoint_public_access  = true
  endpoint_private_access = true

  enable_cluster_creator_admin_permissions = true

  access_entries = local.access_entries

  enabled_log_types = [
    "audit",
    "authenticator"
  ]

  cloudwatch_log_group_retention_in_days = 7

  vpc_id = module.vpc.vpc_id

  subnet_ids = module.vpc.private_subnets

  control_plane_subnet_ids = module.vpc.intra_subnets

  addons = {
    coredns = {
      most_recent = true
    }

    kube-proxy = {
      most_recent = true
    }

    vpc-cni = {
      most_recent    = true
      before_compute = true
    }

    eks-pod-identity-agent = {
      most_recent    = true
      before_compute = true
    }

    metrics-server = {
      most_recent = true
    }

    aws-ebs-csi-driver = {
      most_recent = true

      pod_identity_association = [
        {
          role_arn        = aws_iam_role.ebs_csi.arn
          service_account = "ebs-csi-controller-sa"
        }
      ]
    }
  }

  eks_managed_node_groups = {
    default = {
      ami_type = "AL2023_x86_64_STANDARD"

      instance_types = [
        var.node_instance_type
      ]

      min_size     = var.node_min_size
      max_size     = var.node_max_size
      desired_size = var.node_desired_size

      block_device_mappings = {
        xvda = {
          device_name = "/dev/xvda"

          ebs = {
            volume_size           = var.node_disk_size
            volume_type           = "gp3"
            encrypted             = true
            delete_on_termination = true
          }
        }
      }

      tags = {
        NodeGroup = "default"
      }
    }
  }

  tags = local.tags
}