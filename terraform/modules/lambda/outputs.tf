output "collect_function_name" {
  description = "Имя Lambda функции сбора постов"
  value       = aws_lambda_function.collect.function_name
}

output "collect_function_arn" {
  description = "ARN Lambda функции сбора постов"
  value       = aws_lambda_function.collect.arn
}

output "summarize_function_name" {
  description = "Имя Lambda функции суммаризации"
  value       = aws_lambda_function.summarize.function_name
}

output "summarize_function_arn" {
  description = "ARN Lambda функции суммаризации"
  value       = aws_lambda_function.summarize.arn
}

output "web_function_name" {
  description = "Имя Lambda функции веб-приложения"
  value       = aws_lambda_function.web.function_name
}

output "web_function_arn" {
  description = "ARN Lambda функции веб-приложения"
  value       = aws_lambda_function.web.arn
}

output "lambda_role_arn" {
  description = "ARN IAM роли для Lambda функций"
  value       = aws_iam_role.lambda_role.arn
}

output "lambda_role_name" {
  description = "Имя IAM роли для Lambda функций"
  value       = aws_iam_role.lambda_role.name
}