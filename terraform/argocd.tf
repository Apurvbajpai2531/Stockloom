data "aws_eks_cluster" "stockloom" {
  name = module.eks.cluster_name

  depends_on = [module.eks]
}

data "aws_eks_cluster_auth" "stockloom" {
  name = module.eks.cluster_name

  depends_on = [module.eks]
}

provider "helm" {
  kubernetes = {
    host                   = data.aws_eks_cluster.stockloom.endpoint
    cluster_ca_certificate = base64decode(data.aws_eks_cluster.stockloom.certificate_authority[0].data)
    token                  = data.aws_eks_cluster_auth.stockloom.token
  }
}

resource "helm_release" "argocd" {
  count = var.enable_argocd ? 1 : 0

  name             = "argocd"
  chart            = "${path.module}/charts/argo-cd"
  namespace        = "argocd"
  create_namespace = true

  atomic          = true # install fail hone par Helm khud rollback/cleanup karega
  cleanup_on_fail = true # failed release ko orphan chhodne ke bajaye clean karega
  timeout         = 600  # pods ready hone ke liye enough time (node scaling ke baad bhi safe)
  wait            = true

  depends_on = [
    module.eks
  ]
}