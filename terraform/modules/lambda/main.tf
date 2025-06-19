# Lambda модуль для Reddit AI Digest

# Автоматическое создание deployment пакетов
data "archive_file" "lambda_collect" {
  type        = "zip"
  source_dir  = "${var.lambda_source_path}/lambda_collect"
  output_path = "${path.module}/../../files/lambda_collect.zip"
  excludes    = ["__pycache__", "*.pyc", ".DS_Store", "*.zip"]
}

data "archive_file" "lambda_summarize" {
  type        = "zip"
  source_dir  = "${var.lambda_source_path}/lambda_summarize"
  output_path = "${path.module}/../../files/lambda_summarize.zip"
  excludes    = ["__pycache__", "*.pyc", ".DS_Store", "*.zip"]
}

data "archive_file" "lambda_web" {
  type        = "zip"
  source_dir  = "${path.module}/../../../lambda-web"
  output_path = "${path.module}/../../files/lambda_web.zip"
  excludes    = ["__pycache__", "*.pyc", ".DS_Store", "*.zip", "lambda_deployment.zip", ".env"]
}

# IAM роль для Lambda функций
resource "aws_iam_role" "lambda_role" {
  name = "${var.resource_prefix}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.resource_prefix}-lambda-role"
  }
}

# Политика для Lambda функций
resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.resource_prefix}-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${var.s3_bucket_arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = var.s3_bucket_arn
      },
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = "*"
      }
    ]
  })
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "lambda_logs" {
  for_each = {
    collect   = "${var.resource_prefix}-collect"
    summarize = "${var.resource_prefix}-summarize"
    web       = "${var.resource_prefix}-web-app"
  }

  name              = "/aws/lambda/${each.value}"
  retention_in_days = var.logs_retention_days

  tags = {
    Name = "${each.value}-logs"
  }
}

# Lambda функция сбора постов
resource "aws_lambda_function" "collect" {
  filename         = data.archive_file.lambda_collect.output_path
  function_name    = "reddit-digest-collect"
  role            = aws_iam_role.lambda_role.arn
  handler         = "lambda_function.lambda_handler"
  source_code_hash = data.archive_file.lambda_collect.output_base64sha256
  runtime         = var.lambda_runtime
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory_size

  environment {
    variables = merge(var.env_variables, {
      LAMBDA_SUMMARIZE_FUNCTION_NAME = aws_lambda_function.summarize.function_name
    })
  }

  depends_on = [
    aws_iam_role_policy.lambda_policy,
    aws_cloudwatch_log_group.lambda_logs["collect"]
  ]

  tags = {
    Name = "${var.resource_prefix}-collect"
  }
}

# Lambda функция суммаризации
resource "aws_lambda_function" "summarize" {
  filename         = data.archive_file.lambda_summarize.output_path
  function_name    = "reddit-digest-summarize"
  role            = aws_iam_role.lambda_role.arn
  handler         = "lambda_function.lambda_handler"
  source_code_hash = data.archive_file.lambda_summarize.output_base64sha256
  runtime         = var.lambda_runtime
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory_size

  environment {
    variables = var.env_variables
  }

  depends_on = [
    aws_iam_role_policy.lambda_policy,
    aws_cloudwatch_log_group.lambda_logs["summarize"]
  ]

  tags = {
    Name = "${var.resource_prefix}-summarize"
  }
}

# Lambda функция веб-приложения
resource "aws_lambda_function" "web" {
  filename         = data.archive_file.lambda_web.output_path
  function_name    = "reddit-ai-digest-web-app"
  role            = aws_iam_role.lambda_role.arn
  handler         = "lambda_handler.handler"
  source_code_hash = data.archive_file.lambda_web.output_base64sha256
  runtime         = var.lambda_runtime
  timeout         = 30
  memory_size     = var.lambda_memory_size

  environment {
    variables = {
      S3_BUCKET_NAME    = var.s3_bucket_name
      REDDIT_SUBREDDITS = var.env_variables["REDDIT_SUBREDDITS"]
    }
  }

  depends_on = [
    aws_iam_role_policy.lambda_policy,
    aws_cloudwatch_log_group.lambda_logs["web"]
  ]

  tags = {
    Name = "${var.resource_prefix}-web-app"
  }
}

# Lambda разрешение для функции суммаризации (вызов из функции сбора)
resource "aws_lambda_permission" "allow_collect_to_invoke_summarize" {
  statement_id  = "AllowExecutionFromCollectFunction"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.summarize.function_name
  principal     = "lambda.amazonaws.com"
  source_arn    = aws_lambda_function.collect.arn
}