data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

locals {
  cloudwatch_arn = "arn:aws:logs:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}"
  func_predict_name = "predict_fuel_price"
}

resource "aws_resourcegroups_group" "rg" {
  name = "fuel-forecast-rg"

  resource_query {
    query = <<JSON
{
  "ResourceTypeFilters": ["AWS::AllSupported"],
  "TagFilters": [
    {
      "Key": "app",
      "Values": ["fuel-forecast"]
    }
  ]
}
JSON
  }
}

resource "aws_apigatewayv2_api" "api_gateway" {
  name = "fuel-forecast-gateway"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_stage" "prod_deployment" {
  api_id = aws_apigatewayv2_api.api_gateway.id
  name = "prod"
  auto_deploy = true
  default_route_settings {
    throttling_rate_limit = 1
    throttling_burst_limit = 10
  }
}

resource "aws_apigatewayv2_route" "predict_api_endpoint" {
  api_id = aws_apigatewayv2_api.api_gateway.id
  route_key = "GET /predict"
  target = "integrations/${aws_apigatewayv2_integration.api_predict_integration.id}"
}

resource "aws_iam_role" "lambda_execution_role" {
  name = "fuel-forecast-lambda-execution-role"

  assume_role_policy = jsonencode({
    Version: "2012-10-17",
    Statement: [
        {
            Effect: "Allow",
            Principal: {
                Service: "lambda.amazonaws.com"
            },
            Action: "sts:AssumeRole"
        }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_execution_role_policy" {
  name = "fuel-forecast-execution-role-policy"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version: "2012-10-17",
        Statement: [
          {
            "Effect": "Allow",
            "Action": [
              "logs:CreateLogStream",
              "logs:PutLogEvents"
            ],
            "Resource": [
              "${aws_cloudwatch_log_group.func_predict_log_group.arn}:*"
            ]
          }
        ]
  })
}

data "archive_file" "func_predict_src" {
  type = "zip"
  source_file = "${path.module}/../py/api/predict_fuel_price.py"
  output_path = "${path.module}/../tmp/predict_fuel_price.zip"
}

resource "aws_cloudwatch_log_group" "func_predict_log_group" {
  name = "/aws/lambda/${local.func_predict_name}"
  retention_in_days = 7
}

resource "aws_lambda_function" "func_predict" {
  function_name = local.func_predict_name
  filename = data.archive_file.func_predict_src.output_path

  role = aws_iam_role.lambda_execution_role.arn
  architectures = ["arm64"]
  memory_size = 128
  timeout = 5
  runtime = "python3.14"
  handler = "predict_fuel_price.handler"

  logging_config {
    log_format = "JSON"
    log_group = aws_cloudwatch_log_group.func_predict_log_group.name
  }
}

resource "aws_apigatewayv2_integration" "api_predict_integration" {
  api_id = aws_apigatewayv2_api.api_gateway.id
  integration_type = "AWS_PROXY"
  connection_type = "INTERNET"
  integration_method = "POST"
  integration_uri = aws_lambda_function.func_predict.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_s3_bucket" "s3_backend" {
  bucket = "unclechris-fuel-forecast-storage"
}

resource "aws_s3_bucket" "s3_frontend" {
  bucket = "unclechris-fuel-forecast-frontend"

}

resource "aws_s3_bucket_public_access_block" "s3_frontend_acl_config" {
  bucket = aws_s3_bucket.s3_frontend.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_website_configuration" "s3_frontend_website_config" {
  bucket = aws_s3_bucket.s3_frontend.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "index.html"
  }
}

data "aws_iam_policy_document" "s3_allow_public_access_policy" {
	statement {
        principals {
          type = "*"
          identifiers = ["*"]
        }
        actions = [
            "s3:GetObject"
        ]
        resources = [
            "${aws_s3_bucket.s3_frontend.arn}/*"
        ]
	}
}

resource "aws_s3_bucket_policy" "s3_allow_public_access" {
  bucket = aws_s3_bucket.s3_frontend.id

  policy = data.aws_iam_policy_document.s3_allow_public_access_policy.json
}

resource "aws_s3_object" "s3_public_files" {
  for_each = fileset("${path.module}/../js/dist", "**/*")

  bucket = aws_s3_bucket.s3_frontend.id
  key = each.value
  source = "${path.module}/../js/dist/${each.value}"
  etag = filemd5("${path.module}/../js/dist/${each.value}")
}

resource "aws_dynamodb_table" "fuel_forecast_latest_prices" {
  name = "fuel_forecast_latest_prices"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "station_and_fuel_type"
  range_key = "date"

  attribute {
    name = "station_and_fuel_type"
    type = "S"
  }

  attribute {
    name = "date"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled = true
  }
}
