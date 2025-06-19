output "bucket_name" {
  description = "Имя созданного S3 bucket"
  value       = aws_s3_bucket.main.id
}

output "bucket_arn" {
  description = "ARN созданного S3 bucket"
  value       = aws_s3_bucket.main.arn
}

output "bucket_domain_name" {
  description = "Доменное имя S3 bucket"
  value       = aws_s3_bucket.main.bucket_domain_name
}

output "bucket_regional_domain_name" {
  description = "Региональное доменное имя S3 bucket"
  value       = aws_s3_bucket.main.bucket_regional_domain_name
}