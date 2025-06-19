# Выходные данные после развертывания

output "s3_bucket_name" {
  description = "Имя S3 bucket для хранения данных"
  value       = module.s3.bucket_name
}

output "s3_bucket_arn" {
  description = "ARN S3 bucket"
  value       = module.s3.bucket_arn
}

output "lambda_collect_function_name" {
  description = "Имя Lambda функции сбора постов"
  value       = module.lambda.collect_function_name
}

output "lambda_collect_function_arn" {
  description = "ARN Lambda функции сбора постов"
  value       = module.lambda.collect_function_arn
}

output "lambda_summarize_function_name" {
  description = "Имя Lambda функции суммаризации"
  value       = module.lambda.summarize_function_name
}

output "lambda_summarize_function_arn" {
  description = "ARN Lambda функции суммаризации"
  value       = module.lambda.summarize_function_arn
}

output "lambda_web_function_name" {
  description = "Имя Lambda функции веб-приложения"
  value       = module.lambda.web_function_name
}

output "lambda_web_function_arn" {
  description = "ARN Lambda функции веб-приложения"
  value       = module.lambda.web_function_arn
}

output "api_gateway_url" {
  description = "URL API Gateway для доступа к веб-интерфейсу"
  value       = module.api_gateway.api_url
}

output "eventbridge_rule_name" {
  description = "Имя EventBridge правила для запуска сбора"
  value       = aws_cloudwatch_event_rule.daily_trigger.name
}

output "eventbridge_rule_arn" {
  description = "ARN EventBridge правила"
  value       = aws_cloudwatch_event_rule.daily_trigger.arn
}

output "sns_topic_arn" {
  description = "ARN SNS топика для алертов (если включено)"
  value       = var.enable_monitoring && var.alert_email != "" ? aws_sns_topic.alerts[0].arn : null
}

output "cloudwatch_dashboard_url" {
  description = "URL CloudWatch Dashboard (если включено)"
  value       = var.enable_monitoring ? "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${local.resource_prefix}-dashboard" : null
}

output "monitored_subreddits" {
  description = "Список отслеживаемых Reddit сабреддитов"
  value       = var.reddit_subreddits
}

output "cron_schedule" {
  description = "Расписание запуска сбора постов"
  value       = var.cron_schedule
}

# Полезные команды для управления
output "useful_commands" {
  description = "Полезные команды для управления развертыванием"
  value = {
    test_lambda_collect   = "aws lambda invoke --function-name ${module.lambda.collect_function_name} --payload '{}' response.json"
    view_collect_logs     = "aws logs tail /aws/lambda/${module.lambda.collect_function_name} --follow"
    view_summarize_logs   = "aws logs tail /aws/lambda/${module.lambda.summarize_function_name} --follow"
    view_web_logs         = "aws logs tail /aws/lambda/${module.lambda.web_function_name} --follow"
    list_s3_contents      = "aws s3 ls s3://${module.s3.bucket_name}/ --recursive"
    trigger_manual_run    = "aws events put-events --entries 'Source=manual,DetailType=manual-trigger,Detail=\"{}\"'"
  }
}