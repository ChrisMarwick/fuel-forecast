locals {
  predict_func_name = "predict_price"
}

resource "aws_ecr_repository" "fuel_price" {
  name = "fuel-price"
}

# resource "aws_ecr"

resource "aws_s3_bucket" "s3_backend" {
  bucket = "unclechris-fuel-forecast-storage"
}

module "predict_price_func" {
  source = "./lambda_function"

  function_name = local.predict_func_name
  type = "ECR"
  src = "623791025140.dkr.ecr.ap-southeast-2.amazonaws.com/fuel-price:latest"
  secrets = []
  timeout = 15
  memory_size = 256
  additional_lambda_permissions = ["dynamodb:GetItem", "s3:GetObject"]
}