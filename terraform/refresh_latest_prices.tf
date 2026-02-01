locals {
  refresh_func_name = "refresh_latest_prices"
}

# *** Roles ***

resource "aws_iam_role" "scheduler_role" {
  name = "${local.refresh_func_name}_role"

  assume_role_policy = jsonencode({
    Version: "2012-10-17",
    Statement: [
        {
            Effect: "Allow",
            Principal: {
                Service: "scheduler.amazonaws.com"
            },
            Action: "sts:AssumeRole"
        },
    ]
  })
}

resource "aws_iam_role_policy" "scheduler_role_policy" {
  name = "${local.refresh_func_name}_role_policy"
  role = aws_iam_role.scheduler_role.id

  policy = jsonencode({
    Version: "2012-10-17",
    Statement: [
      {
        "Effect": "Allow",
        "Action": ["lambda:InvokeFunction"]
        "Resource": [module.refresh_latest_prices_func.arn]
      }
    ]
  })
}

# *** Main resources ***

module "refresh_latest_prices_func" {
  source = "./lambda_function"

  function_name = local.refresh_func_name
  src_path = "${path.module}/../py/functions/${local.refresh_func_name}"
  secrets = ["nsw_gov_api_key", "nsw_gov_api_secret"]
  timeout = 300
  additional_lambda_permissions = ["dynamodb:BatchWriteItem"]
}

resource "aws_scheduler_schedule" "schedule" {
  name = "${local.refresh_func_name}_schedule"
  group_name = "default"
  schedule_expression = "rate(1 days)"
  schedule_expression_timezone = "Australia/Sydney"
  start_date = "2026-02-01T15:00:00Z"

  flexible_time_window {
    mode = "FLEXIBLE"
    maximum_window_in_minutes = 15
  }

  target {
    arn = module.refresh_latest_prices_func.arn
    role_arn = aws_iam_role.scheduler_role.arn

    retry_policy {
      maximum_retry_attempts = 0
    }
  }
}

