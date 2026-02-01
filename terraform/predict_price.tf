locals {
  predict_func_name = "predict_price"
}

resource "aws_s3_bucket" "s3_backend" {
  bucket = "unclechris-fuel-forecast-storage"
}

module "predict_price_func" {
  source = "./lambda_function"

  function_name = local.predict_func_name
  src_path = "${path.module}/../py/functions/${local.predict_func_name}"
  secrets = []
  additional_lambda_permissions = ["dynamodb:GetItem", "s3:GetObject"]
}