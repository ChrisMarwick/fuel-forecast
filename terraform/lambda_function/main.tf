variable "function_name" {
  type = string
}

variable "src_path" {
  type = string
}

variable "secrets" {
  type = list(string)
  default = []
}

variable "timeout" {
  type = number
  default = 5
}

variable "additional_lambda_permissions" {
  type = list(string)
  default = []
}

# variable "api_gateway_id" {
#   type = string
# }
#
# variable "api_endpoint_name" {
#   type = string
# }
#
# variable "api_endpoint_verb" {
#   type = string
#   default = "GET"
# }

# *** Roles ***

resource "aws_iam_role" "lambda_execution_role" {
  name = "${var.function_name}-lambda-execution-role"

  assume_role_policy = jsonencode({
    Version: "2012-10-17",
    Statement: [
        {
            Effect: "Allow",
            Principal: {
                Service: "lambda.amazonaws.com"
            },
            Action: "sts:AssumeRole"
        },
    ]
  })
}

resource "aws_iam_role_policy" "lambda_execution_role_policy" {
  name = "${var.function_name}-lambda-execution-role-policy"
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
          "${aws_cloudwatch_log_group.log_group.arn}:*"
        ]
      },
      length(var.secrets) > 0 ? {
        "Effect": "Allow",
        "Action": [
          "secretsmanager:GetSecretValue"
        ],
        "Resource": [for secret in aws_secretsmanager_secret.lambda_secrets: secret.arn]
      } : null,
      {
        "Effect": "Allow",
        "Action": [
          for permission in var.additional_lambda_permissions: permission
        ],
        "Resource": "*"
      }
    ]
  })
}

# *** Main resources ***

resource "aws_secretsmanager_secret" "lambda_secrets" {
  for_each = toset(var.secrets)

  name = "${var.function_name}_${each.value}"
  recovery_window_in_days = 0
}

resource "aws_cloudwatch_log_group" "log_group" {
  name = "/aws/lambda/${var.function_name}"
  retention_in_days = 7
}

data "archive_file" "lambda_src" {
  type = "zip"
  output_path = "${path.module}/tmp/${var.function_name}.zip"
  source_dir = var.src_path
  excludes = [".venv", ".idea"]
}

resource "aws_lambda_function" "lambda" {
  function_name = var.function_name
  filename = data.archive_file.lambda_src.output_path

  role = aws_iam_role.lambda_execution_role.arn
  architectures = ["arm64"]
  memory_size = 128
  timeout = var.timeout
  runtime = "python3.14"
  handler = "${var.function_name}.handler"
  source_code_hash = data.archive_file.lambda_src.output_base64sha256

  logging_config {
    log_format = "JSON"
    log_group = aws_cloudwatch_log_group.log_group.name
  }
}

# resource "aws_apigatewayv2_integration" "api_integration" {
#   api_id = var.api_gateway_id
#   integration_type = "AWS_PROXY"
#   connection_type = "INTERNET"
#   integration_method = "POST"
#   integration_uri = aws_lambda_function.lambda.invoke_arn
#   payload_format_version = "2.0"
# }
#
# resource "aws_apigatewayv2_route" "api_endpoint" {
#   api_id = var.api_gateway_id
#   route_key = "${var.api_endpoint_verb} /${var.api_endpoint_name}"
#   target = "integrations/${aws_apigatewayv2_integration.api_integration.id}"
# }

output "arn" {
  value = aws_lambda_function.lambda.arn
}
