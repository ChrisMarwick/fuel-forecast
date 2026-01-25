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
            "Action": "logs:CreateLogGroup",
            "Resource": "${local.cloudwatch_arn}:*"
          },
          {
            "Effect": "Allow",
            "Action": [
              "logs:CreateLogStream",
              "logs:PutLogEvents"
            ],
            "Resource": [
              "${local.cloudwatch_arn}:log-group:/aws/lambda/${local.func_predict_name}:*"
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

resource "aws_lambda_function" "func_predict" {
  function_name = local.func_predict_name
  filename = data.archive_file.func_predict_src.output_path

  role = aws_iam_role.lambda_execution_role.arn
  architectures = ["arm64"]
  memory_size = 128
  timeout = 5
  runtime = "python3.14"
  handler = "handler"
}

resource "aws_apigatewayv2_integration" "api_predict_integration" {
  api_id = aws_apigatewayv2_api.api_gateway.id
  integration_type = "AWS_PROXY"
  connection_type = "INTERNET"
  integration_method = "POST"
  integration_uri = aws_lambda_function.func_predict.invoke_arn
}

resource "aws_s3_bucket" "s3" {
  bucket = "unclechris-fuel-forecast-storage"
}