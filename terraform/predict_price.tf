locals {
  predict_func_name = "predict_price"
}

resource "aws_ecr_repository" "container_repo" {
  name = "fuel-price"
}

data "aws_ecr_lifecycle_policy_document" "lifecycle_policy_doc" {
  rule {
    priority = 1
    description = "Only keep the latest image"
    selection {
      tag_status = "any"
      count_type = "imageCountMoreThan"
      count_number = 1
    }
  }
}

resource "aws_ecr_lifecycle_policy" "container_repo_lifecycle_policy" {
  repository = aws_ecr_repository.container_repo.name

  policy = data.aws_ecr_lifecycle_policy_document.lifecycle_policy_doc.json
}

resource "aws_s3_bucket" "s3_backend" {
  bucket = "unclechris-fuel-forecast-storage"
}

module "predict_price_func" {
  source = "./lambda_function"

  function_name = local.predict_func_name
  type = "ECR"
  src = "623791025140.dkr.ecr.ap-southeast-2.amazonaws.com/fuel-price:latest"
  secrets = []
  timeout = 30
  memory_size = 1024
  additional_lambda_permissions = ["dynamodb:GetItem", "s3:GetObject"]
}