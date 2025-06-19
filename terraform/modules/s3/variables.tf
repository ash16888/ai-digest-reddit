variable "bucket_name" {
  description = "Имя S3 bucket"
  type        = string
}

variable "environment" {
  description = "Окружение развертывания"
  type        = string
}

variable "resource_prefix" {
  description = "Префикс для именования ресурсов"
  type        = string
}