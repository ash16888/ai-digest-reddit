variable "resource_prefix" {
  description = "Префикс для именования ресурсов"
  type        = string
}

variable "environment" {
  description = "Окружение развертывания"
  type        = string
}

variable "lambda_function_arn" {
  description = "ARN Lambda функции веб-приложения"
  type        = string
}

variable "lambda_function_name" {
  description = "Имя Lambda функции веб-приложения"
  type        = string
}

variable "s3_bucket_name" {
  description = "Имя S3 bucket для хранения данных"
  type        = string
}

variable "reddit_subreddits" {
  description = "Строка с списком Reddit сабреддитов"
  type        = string
}

variable "custom_domain_name" {
  description = "Custom domain name для API (опционально)"
  type        = string
  default     = ""
}

variable "certificate_arn" {
  description = "ARN ACM сертификата для custom domain (если используется)"
  type        = string
  default     = ""
}