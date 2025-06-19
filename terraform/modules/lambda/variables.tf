variable "resource_prefix" {
  description = "Префикс для именования ресурсов"
  type        = string
}

variable "environment" {
  description = "Окружение развертывания"
  type        = string
}

variable "lambda_runtime" {
  description = "Python runtime версия для Lambda"
  type        = string
}

variable "lambda_memory_size" {
  description = "Размер памяти для Lambda функций (MB)"
  type        = number
}

variable "lambda_timeout" {
  description = "Таймаут для Lambda функций (секунды)"
  type        = number
}

variable "s3_bucket_name" {
  description = "Имя S3 bucket для хранения данных"
  type        = string
}

variable "s3_bucket_arn" {
  description = "ARN S3 bucket"
  type        = string
}

variable "logs_retention_days" {
  description = "Количество дней хранения логов"
  type        = number
}

variable "env_variables" {
  description = "Переменные окружения для Lambda функций"
  type        = map(string)
}

variable "lambda_source_path" {
  description = "Путь к исходному коду Lambda функций"
  type        = string
}