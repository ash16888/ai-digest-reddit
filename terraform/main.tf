# Основная конфигурация для Reddit AI Digest

# S3 bucket для хранения данных
module "s3" {
  source = "./modules/s3"
  
  bucket_name     = local.s3_bucket_name
  environment     = var.environment
  resource_prefix = local.resource_prefix
}

# Lambda модуль для функций сбора и суммаризации
module "lambda" {
  source = "./modules/lambda"
  
  resource_prefix      = local.resource_prefix
  environment          = var.environment
  lambda_runtime       = var.lambda_runtime
  lambda_memory_size   = var.lambda_memory_size
  lambda_timeout       = var.lambda_timeout
  s3_bucket_name       = module.s3.bucket_name
  s3_bucket_arn        = module.s3.bucket_arn
  logs_retention_days  = var.s3_logs_retention_days
  
  # Переменные окружения для Lambda
  env_variables = {
    # Reddit API
    REDDIT_CLIENT_ID     = var.reddit_client_id
    REDDIT_CLIENT_SECRET = var.reddit_client_secret
    REDDIT_USER_AGENT    = var.reddit_user_agent
    REDDIT_SUBREDDITS    = local.reddit_subreddits_string
    
    # OpenAI API
    OPENAI_API_KEY = var.openai_api_key
    
    # S3
    S3_BUCKET_NAME = module.s3.bucket_name
  }
  
  # Путь к исходному коду Lambda функций
  lambda_source_path = "${path.module}/../lambda-cron"
}

# EventBridge правило для запуска Lambda функции сбора
resource "aws_cloudwatch_event_rule" "daily_trigger" {
  name                = "reddit-digest-daily-trigger"
  description         = "Ежедневный запуск сбора Reddit постов"
  schedule_expression = var.cron_schedule
  
  tags = {
    Name = "${local.resource_prefix}-daily-trigger"
  }
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.daily_trigger.name
  target_id = "LambdaTarget"
  arn       = module.lambda.collect_function_arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda.collect_function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_trigger.arn
}

# API Gateway для веб-интерфейса
module "api_gateway" {
  source = "./modules/api_gateway"
  
  resource_prefix        = local.resource_prefix
  environment            = var.environment
  lambda_function_arn    = module.lambda.web_function_arn
  lambda_function_name   = module.lambda.web_function_name
  s3_bucket_name         = module.s3.bucket_name
  reddit_subreddits      = local.reddit_subreddits_string
}

# CloudWatch мониторинг и алерты (если включено)
resource "aws_sns_topic" "alerts" {
  count = var.enable_monitoring && var.alert_email != "" ? 1 : 0
  
  name = "${local.resource_prefix}-alerts"
  
  tags = {
    Name = "${local.resource_prefix}-alerts"
  }
}

resource "aws_sns_topic_subscription" "email_alerts" {
  count = var.enable_monitoring && var.alert_email != "" ? 1 : 0
  
  topic_arn = aws_sns_topic.alerts[0].arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# CloudWatch алерты для Lambda функций
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  for_each = var.enable_monitoring ? {
    collect   = module.lambda.collect_function_name
    summarize = module.lambda.summarize_function_name
    web       = module.lambda.web_function_name
  } : {}
  
  alarm_name          = "${each.value}-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name        = "Errors"
  namespace          = "AWS/Lambda"
  period             = "300"
  statistic          = "Sum"
  threshold          = "5"
  alarm_description  = "Alarm when Lambda function ${each.key} has errors"
  
  dimensions = {
    FunctionName = each.value
  }
  
  alarm_actions = var.alert_email != "" ? [aws_sns_topic.alerts[0].arn] : []
  
  tags = {
    Name = "${each.value}-errors-alarm"
  }
}

# CloudWatch Dashboard для мониторинга
resource "aws_cloudwatch_dashboard" "main" {
  count = var.enable_monitoring ? 1 : 0
  
  dashboard_name = "${local.resource_prefix}-dashboard"
  
  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        
        properties = {
          metrics = [
            ["AWS/Lambda", "Invocations", "FunctionName", module.lambda.collect_function_name],
            [".", ".", ".", module.lambda.summarize_function_name],
            [".", ".", ".", module.lambda.web_function_name]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "Lambda Invocations"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        
        properties = {
          metrics = [
            ["AWS/Lambda", "Errors", "FunctionName", module.lambda.collect_function_name],
            [".", ".", ".", module.lambda.summarize_function_name],
            [".", ".", ".", module.lambda.web_function_name]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "Lambda Errors"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        
        properties = {
          metrics = [
            ["AWS/Lambda", "Duration", "FunctionName", module.lambda.collect_function_name],
            [".", ".", ".", module.lambda.summarize_function_name],
            [".", ".", ".", module.lambda.web_function_name]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "Lambda Duration (ms)"
        }
      }
    ]
  })
}