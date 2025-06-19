# Reddit Digest AWS Lambda

Автоматизированная система сбора и анализа постов Reddit с развертыванием в AWS Lambda.

## Архитектура

```text
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   EventBridge   │───▶│ Lambda Collect   │───▶│ Lambda Summarize│
│   (Cron: 1AM)   │    │ (Сбор + фильтр)  │    │   (Дайджест)    │
└─────────────────┘    └──────────┬───────┘    └─────────┬───────┘
                                  │                       │
                            ┌─────▼──────┐         ┌──────▼──────┐
                            │ S3: data/  │         │ S3: reports/│
                            └────────────┘         └─────────────┘
```

## Компоненты

### Lambda Функции

1. **reddit-digest-collect** - Сбор и фильтрация постов
   - Собирает посты из 7 сабреддитов за вчерашний день
   - Фильтрует по популярности (score ≥ 30 или comments ≥ 30)
   - Исключает мемы и юмористический контент
   - Сохраняет в S3: `data/all_posts_YYYY-MM-DD.json` и `data/posts_YYYY-MM-DD.json`
   - Запускает функцию суммаризации

2. **reddit-digest-summarize** - Генерация дайджеста
   - Использует OpenAI API для создания структурированного обзора
   - Анализирует тренды в AI сообществе
   - Сохраняет дайджест в S3: `reports/digest_YYYY-MM-DD.md`

### Инфраструктура

- **S3 Bucket**: `ai-reddit-digest`
  - `data/` - сырые и отфильтрованные данные постов
  - `reports/` - сгенерированные дайджесты
- **EventBridge Rule**: ежедневный запуск в 01:00 UTC
- **IAM Roles**: минимальные права доступа для каждой функции
- **CloudWatch Logs**: логирование выполнения

## Быстрый старт

### Предварительные требования

1. **Python 3.12+** установлен (для локальной сборки)
2. **API ключи**:
   - Reddit API (client_id, client_secret)
   - OpenAI API key
3. **Terraform** для развертывания (см. ../terraform/README.md)

### Получение Reddit API ключей

1. Перейдите на <https://www.reddit.com/prefs/apps>
2. Создайте новое приложение типа "script"
3. Скопируйте client_id и client_secret

### Развертывание

⚠️ **ВАЖНО**: Развертывание теперь выполняется через Terraform!

```bash
# 1. Сборка Lambda пакетов (опционально, Terraform делает это автоматически)
./build.sh

# 2. Развертывание через Terraform
cd ../terraform
terraform init
terraform apply
```

Подробные инструкции по развертыванию см. в [../terraform/README.md](../terraform/README.md)

### Мониторинг

После развертывания через Terraform используйте:

```bash
# Получить все полезные команды
cd ../terraform
terraform output useful_commands
```

Команды будут включать все необходимые инструкции для мониторинга и тестирования.

## Конфигурация

### Переменные окружения

Все переменные окружения теперь настраиваются через Terraform. См. файл `terraform/terraform.tfvars.example` для полного списка настроек.

### Параметры Lambda

Параметры Lambda функций (память, таймаут, расписание) настраиваются в файле `terraform/terraform.tfvars`.

### Мониторируемые сабреддиты

- r/ChatGPT
- r/OpenAI  
- r/ClaudeAI
- r/Bard
- r/GeminiAI
- r/DeepSeek
- r/grok

## Стоимость

Примерная стоимость работы в месяц:

- **Lambda**: ~$0.50 (30 запусков × 2 функции)
- **S3**: ~$0.10 (хранение данных)
- **CloudWatch**: ~$0.05 (логи)
- **OpenAI API**: ~$0 (зависит от объема постов)

**Итого**: ~$1/месяц

## Ручное тестирование

После развертывания через Terraform:

```bash
# Получите команды для тестирования
cd ../terraform
terraform output useful_commands

# Там будут команды для:
# - test_lambda_collect - тестирование функции сбора
# - и другие полезные команды
```

Для тестирования функции суммаризации с конкретной датой, создайте payload.json с нужными параметрами.

## Управление

### Обновление кода

```bash
# Terraform автоматически пересоберет и обновит Lambda функции
cd ../terraform
terraform apply
```

### Удаление ресурсов

```bash
# Удаление всех ресурсов через Terraform
cd ../terraform
terraform destroy
```

### Изменение расписания

Отредактируйте переменную `cron_schedule` в файле `terraform/terraform.tfvars` и примените изменения:

```bash
cd ../terraform
terraform apply
```

## Структура проекта

```text
lambda-cron/
├── lambda_collect/         # Функция сбора постов
│   ├── lambda_function.py  # Основной handler
│   ├── fetch_posts.py      # Сбор постов
│   ├── filter_posts.py     # Фильтрация
│   ├── utils.py            # Утилиты и S3
│   └── requirements.txt    # Зависимости
├── lambda_summarize/       # Функция суммаризации
│   ├── lambda_function.py  # Основной handler
│   ├── summarize.py        # OpenAI интеграция
│   ├── utils.py            # Утилиты и S3
│   └── requirements.txt    # Зависимости
├── build.sh               # Скрипт сборки (опционально)
├── deploy.sh              # Устаревший скрипт (см. terraform/)
└── README.md              # Документация
```

## Поддержка

При возникновении проблем:

1. Проверьте логи Lambda функций
2. Убедитесь, что API ключи корректны
3. Проверьте права доступа IAM
4. Убедитесь, что S3 бакет доступен
