# S3 модуль для хранения данных Reddit AI Digest

# S3 bucket для хранения данных
resource "aws_s3_bucket" "main" {
  bucket = var.bucket_name

  tags = {
    Name        = var.bucket_name
    Environment = var.environment
    Purpose     = "Reddit AI Digest Data Storage"
  }
}

# Версионирование для bucket
resource "aws_s3_bucket_versioning" "main" {
  bucket = aws_s3_bucket.main.id

  versioning_configuration {
    status = "Suspended"
  }
}

# Шифрование для bucket
resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  bucket = aws_s3_bucket.main.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Блокировка публичного доступа
resource "aws_s3_bucket_public_access_block" "main" {
  bucket = aws_s3_bucket.main.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle правило для удаления старых данных (опционально)
resource "aws_s3_bucket_lifecycle_configuration" "main" {
  bucket = aws_s3_bucket.main.id

  rule {
    id     = "delete-old-data"
    status = "Enabled"

    # Удаление сырых данных через 30 дней

    expiration {
      days = 30
    }

    filter {
      prefix = "data/"
    }
  }

  rule {
    id     = "keep-reports"
    status = "Enabled"

    expiration {
      days = 60
    }

    filter {
      prefix = "reports/"
    }
  }
}

# CORS конфигурация для веб-доступа
resource "aws_s3_bucket_cors_configuration" "main" {
  bucket = aws_s3_bucket.main.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "HEAD"]
    allowed_origins = ["*"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}