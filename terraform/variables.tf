# Основные переменные проекта
variable "project_name" {
  description = "Название проекта"
  type        = string
  default     = "reddit-ai-digest"
}

variable "environment" {
  description = "Окружение развертывания (dev/staging/prod)"
  type        = string
  default     = "prod"
}

variable "aws_region" {
  description = "AWS регион для развертывания"
  type        = string
  default     = "eu-central-1"
}

# Reddit API конфигурация
variable "reddit_client_id" {
  description = "Reddit API Client ID"
  type        = string
  sensitive   = true
}

variable "reddit_client_secret" {
  description = "Reddit API Client Secret"
  type        = string
  sensitive   = true
}

variable "reddit_user_agent" {
  description = "Reddit API User Agent"
  type        = string
  default     = "reddit-digest-lambda/1.0"
}

variable "reddit_subreddits" {
  description = "Список Reddit сабреддитов для мониторинга"
  type        = list(string)
  default     = ["ChatGPT", "OpenAI", "ClaudeAI", "Bard", "GeminiAI", "DeepSeek", "grok"]
}

# OpenAI API конфигурация
variable "openai_api_key" {
  description = "OpenAI API ключ для генерации дайджестов"
  type        = string
  sensitive   = true
}

# Lambda конфигурация
variable "lambda_runtime" {
  description = "Python runtime версия для Lambda"
  type        = string
  default     = "python3.12"
}

variable "lambda_memory_size" {
  description = "Размер памяти для Lambda функций (MB)"
  type        = number
  default     = 512
}

variable "lambda_timeout" {
  description = "Таймаут для Lambda функций (секунды)"
  type        = number
  default     = 300
}

# Расписание cron
variable "cron_schedule" {
  description = "Расписание запуска Lambda функции сбора (cron expression)"
  type        = string
  default     = "cron(0 1 * * ? *)" # 1:00 UTC ежедневно
}

# S3 конфигурация
variable "s3_bucket_name" {
  description = "Имя S3 bucket для хранения данных. Если не указано, будет создано автоматически"
  type        = string
  default     = ""
}

variable "s3_logs_retention_days" {
  description = "Количество дней хранения логов в CloudWatch"
  type        = number
  default     = 30
}

# Мониторинг и алерты
variable "enable_monitoring" {
  description = "Включить CloudWatch мониторинг и алерты"
  type        = bool
  default     = true
}

variable "alert_email" {
  description = "Email для получения уведомлений об ошибках (необязательно)"
  type        = string
  default     = ""
}

# Локальные переменные
locals {
  # Имя S3 bucket
  s3_bucket_name = var.s3_bucket_name != "" ? var.s3_bucket_name : "${var.project_name}-${var.environment}-${data.aws_caller_identity.current.account_id}"
  
  # Префикс для именования ресурсов
  resource_prefix = "${var.project_name}-${var.environment}"
  
  # Общие теги для всех ресурсов
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Repository  = "reddit_script"
  }
  
  # Строка сабреддитов для переменной окружения
  reddit_subreddits_string = join(",", var.reddit_subreddits)
}

# Получение текущего аккаунта AWS
data "aws_caller_identity" "current" {}