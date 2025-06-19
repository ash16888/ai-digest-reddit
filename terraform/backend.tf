# Конфигурация backend для хранения Terraform state в S3
# 
# ВАЖНО: Перед первым запуском terraform init необходимо:
# 1. Создать S3 bucket для state файлов
# 2. Включить версионирование для bucket
# 3. Заменить placeholder значения ниже на реальные
#
# Создайте bucket через AWS Console или AWS CLI перед запуском terraform init
# Имя bucket: terraform-state-reddit-ai-digest-[your_id]
# Включите версионирование для bucket

terraform {
  backend "s3" {
    # Имя S3 bucket для хранения state
    # Замените [account-id] на ваш AWS account ID
    bucket = "terraform-state-reddit-ai-digest-[your-id]"
    
    # Путь к state файлу внутри bucket
    key    = "prod/terraform.tfstate"
    
    # AWS регион где находится bucket
    region = "eu-central-1"
    
    # Включить шифрование state файла
    encrypt = true
    
    # Опционально: профиль AWS CLI для доступа к bucket
    # profile = "default"
  }
}