output "api_id" {
  description = "ID API Gateway"
  value       = aws_apigatewayv2_api.main.id
}

output "api_endpoint" {
  description = "Endpoint URL API Gateway"
  value       = aws_apigatewayv2_api.main.api_endpoint
}

output "api_url" {
  description = "Полный URL для доступа к веб-интерфейсу"
  value       = "${aws_apigatewayv2_api.main.api_endpoint}/${aws_apigatewayv2_stage.prod.name}"
}

output "stage_name" {
  description = "Имя stage"
  value       = aws_apigatewayv2_stage.prod.name
}

output "execution_arn" {
  description = "Execution ARN для API Gateway"
  value       = aws_apigatewayv2_api.main.execution_arn
}

output "custom_domain_url" {
  description = "URL с custom domain (если настроен)"
  value       = var.custom_domain_name != "" ? "https://${var.custom_domain_name}" : null
}