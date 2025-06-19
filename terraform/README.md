# Reddit AI Digest - Terraform Infrastructure

Этот каталог содержит Terraform конфигурацию для развертывания Reddit AI Digest в AWS.

## 🚀 Быстрый старт

### Предварительные требования

1. **Terraform** >= 1.5.0
2. **AWS CLI** настроенный с правильными учетными данными
3. **Reddit API** ключи (получите на https://www.reddit.com/prefs/apps)
4. **OpenAI API** ключ (получите на https://platform.openai.com/api-keys)

### Шаги развертывания

1. **Создайте S3 bucket для Terraform state:**

   Terraform требует S3 bucket для хранения состояния. Создайте его вручную через AWS Console или AWS CLI:
   
   - **Имя bucket**: `terraform-state-reddit-ai-digest-YOUR_ACCOUNT_ID`
   - **Включите версионирование**: Да
   - **Регион**: тот же, что и для развертывания (по умолчанию eu-central-1)

2. **Обновите backend конфигурацию:**
Отредактируйте `backend.tf` и замените `[account-id]` на ваш AWS account ID.

3. **Создайте файл с переменными:**
```bash
cp terraform.tfvars.example terraform.tfvars
# Отредактируйте terraform.tfvars и заполните все необходимые значения
```

4. **Инициализируйте Terraform:**
```bash
terraform init
```

5. **Проверьте план развертывания:**
```bash
terraform plan
```

6. **Примените конфигурацию:**
```bash
terraform apply
```

## 📁 Структура проекта

```
terraform/
├── main.tf                    # Основная конфигурация ресурсов
├── variables.tf              # Определение переменных
├── outputs.tf               # Выходные данные
├── versions.tf              # Версии Terraform и провайдеров
├── backend.tf               # Конфигурация S3 backend
├── terraform.tfvars.example # Пример файла переменных
└── modules/                 # Terraform модули
    ├── lambda/             # Lambda функции
    ├── s3/                # S3 bucket
    └── api_gateway/       # API Gateway
```

## 🔧 Основные компоненты

### Lambda функции
- **collect**: Сбор постов из Reddit (запускается по расписанию)
- **summarize**: Генерация дайджестов с помощью OpenAI
- **web-app**: FastAPI веб-интерфейс

### Автоматическая сборка пакетов
Terraform автоматически создает deployment пакеты для Lambda функций используя `archive_file` data source. При изменении кода, пакеты пересобираются автоматически.

### Мониторинг
- CloudWatch Dashboard для отслеживания метрик
- CloudWatch Alarms для оповещений об ошибках
- SNS топик для email уведомлений (опционально)

## 📋 Управление сабреддитами

Список отслеживаемых сабреддитов настраивается через переменную `reddit_subreddits` в файле `terraform.tfvars`:

```hcl
reddit_subreddits = [
  "ChatGPT",
  "OpenAI", 
  "ClaudeAI",
  "Bard",
  "GeminiAI",
  "DeepSeek",
  "grok",
  "LocalLLaMA"  # Добавить новый сабреддит
]
```

После изменения списка выполните:
```bash
terraform apply -target=module.lambda
```

## 🔄 Обновление инфраструктуры

### Обновление кода Lambda функций
```bash
# Terraform автоматически пересоберет пакеты и обновит функции
terraform apply
```

### Изменение расписания
Отредактируйте `cron_schedule` в `terraform.tfvars`:
```hcl
# Примеры:
cron_schedule = "cron(0 1 * * ? *)"   # Ежедневно в 1:00 UTC
cron_schedule = "cron(0 */6 * * ? *)" # Каждые 6 часов
cron_schedule = "cron(0 9 ? * MON *)" # Каждый понедельник в 9:00 UTC
```

### Изменение ресурсов Lambda
```hcl
# В terraform.tfvars
lambda_memory_size = 1024  # Увеличить память
lambda_timeout = 600       # Увеличить таймаут
```

## 🔍 Полезные команды

После развертывания Terraform выведет полезные команды:

```bash
# Получить все полезные команды
terraform output useful_commands

# Команды будут включать:
# - Тестирование Lambda функций
# - Просмотр логов в реальном времени
# - Работу с S3 bucket
# - Ручной запуск процесса сбора
```

## 🚨 Мониторинг и алерты

### Включение email уведомлений
```hcl
# В terraform.tfvars
enable_monitoring = true
alert_email = "your-email@example.com"
```

### CloudWatch Dashboard
URL dashboard будет выведен после развертывания. Отслеживайте:
- Количество вызовов Lambda
- Ошибки выполнения
- Длительность выполнения
- Использование памяти

## 💰 Оценка стоимости

При стандартном использовании (1 запуск в день):
- Lambda: ~$0.50/месяц
- S3: ~$0.10/месяц
- CloudWatch: ~$0.05/месяц
- API Gateway: ~$0.01/месяц
- **Итого: < $1/месяц**

## 🗑️ Удаление инфраструктуры

Для полного удаления всех ресурсов:
```bash
# 1. Получите имя S3 bucket
terraform output s3_bucket_name

# 2. Очистите bucket (замените BUCKET-NAME на реальное имя)
# Внимание: это удалит все данные!
aws s3 rm s3://BUCKET-NAME --recursive

# 3. Удалите всю инфраструктуру
terraform destroy
```

## 🔐 Безопасность

- Все sensitive переменные помечены как `sensitive` в Terraform
- API ключи хранятся в переменных окружения Lambda
- S3 bucket защищен от публичного доступа
- IAM роли имеют минимальные необходимые права
- State файл шифруется в S3

## 🛠️ Решение проблем

### Ошибка "Error creating Lambda function"
Убедитесь, что deployment пакеты создались:
```bash
ls terraform/files/
# Должны быть файлы: lambda_collect.zip, lambda_summarize.zip, lambda_web.zip
```

### Ошибка "AccessDenied" при работе с S3
Проверьте IAM права текущего пользователя AWS CLI.

### Lambda функция не запускается по расписанию
Проверьте EventBridge правило:
```bash
# Получите имя правила
terraform output eventbridge_rule_name

# Затем проверьте его состояние (замените RULE-NAME)
aws events describe-rule --name RULE-NAME
```

## 📚 Дополнительная документация

- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS Lambda с Terraform](https://learn.hashicorp.com/tutorials/terraform/lambda-api-gateway)
- [EventBridge Cron Expressions](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-create-rule-schedule.html)