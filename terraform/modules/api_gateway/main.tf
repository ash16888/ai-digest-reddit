# API Gateway модуль для веб-интерфейса Reddit AI Digest

# HTTP API Gateway
resource "aws_apigatewayv2_api" "main" {
  name          = "${var.resource_prefix}-api"
  protocol_type = "HTTP"
  description   = "API Gateway для Reddit AI Digest веб-интерфейса"

  cors_configuration {
    allow_origins     = ["*"]
    allow_methods     = ["GET", "POST", "OPTIONS"]
    allow_headers     = ["content-type", "x-amz-date", "authorization", "x-api-key"]
    expose_headers    = ["x-amz-date"]
    max_age           = 300
    allow_credentials = false
  }

  tags = {
    Name        = "${var.resource_prefix}-api"
    Environment = var.environment
  }
}

# Lambda интеграция
resource "aws_apigatewayv2_integration" "lambda" {
  api_id = aws_apigatewayv2_api.main.id

  integration_type       = "AWS_PROXY"
  integration_uri        = var.lambda_function_arn
  payload_format_version = "2.0"
}

# Маршрут для всех запросов
resource "aws_apigatewayv2_route" "default" {
  api_id = aws_apigatewayv2_api.main.id

  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

# Stage для развертывания
resource "aws_apigatewayv2_stage" "prod" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = "prod"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_logs.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      sourceIp       = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      protocol       = "$context.protocol"
      httpMethod     = "$context.httpMethod"
      resourcePath   = "$context.resourcePath"
      routeKey       = "$context.routeKey"
      status         = "$context.status"
      responseLength = "$context.responseLength"
      error          = "$context.error.message"
    })
  }

  tags = {
    Name        = "${var.resource_prefix}-api-prod"
    Environment = var.environment
  }
}

# CloudWatch Log Group для API Gateway
resource "aws_cloudwatch_log_group" "api_logs" {
  name              = "/aws/apigateway/${var.resource_prefix}-api"
  retention_in_days = 30

  tags = {
    Name = "${var.resource_prefix}-api-logs"
  }
}

# Lambda разрешение для API Gateway
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

# Throttling настройки
resource "aws_apigatewayv2_api_mapping" "main" {
  api_id      = aws_apigatewayv2_api.main.id
  domain_name = aws_apigatewayv2_domain_name.main[0].id
  stage       = aws_apigatewayv2_stage.prod.id

  count = var.custom_domain_name != "" ? 1 : 0
}

# Custom domain (опционально)
resource "aws_apigatewayv2_domain_name" "main" {
  count = var.custom_domain_name != "" ? 1 : 0

  domain_name = var.custom_domain_name

  domain_name_configuration {
    certificate_arn = var.certificate_arn
    endpoint_type   = "REGIONAL"
    security_policy = "TLS_1_2"
  }

  tags = {
    Name        = "${var.resource_prefix}-api-domain"
    Environment = var.environment
  }
}