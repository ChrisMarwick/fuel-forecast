data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

locals {

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
