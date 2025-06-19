# Reddit AI Digest

Автоматизированная система для создания ежедневных дайджестов новостей и обсуждений в области искусственного интеллекта на основе контента из Reddit. Система ориентирована на русскоязычную аудиторию и предоставляет структурированные обзоры самых популярных постов из ключевых AI-сабреддитов.

## 🎯 Особенности

- **Автоматический сбор** из 7 ключевых AI-сабреддитов
- **Интеллектуальная фильтрация** мемов и несущественного контента
- **Генерация дайджестов** на русском языке с использованием OpenAI API
- **Веб-интерфейс** для просмотра архива дайджестов
- **AWS Lambda развертывание** для полной автоматизации

## 📋 Отслеживаемые сабреддиты

- r/ChatGPT
- r/OpenAI
- r/ClaudeAI
- r/Bard (Google Gemini)
- r/GeminiAI
- r/DeepSeek
- r/grok

## 🏗️ Архитектура

Проект состоит из двух основных компонентов:

### 1. AWS Lambda (lambda-cron/)
Полностью serverless решение для автоматического сбора и обработки данных:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   EventBridge   │───▶│ Lambda Collect   │───▶│ Lambda Summarize│
│   (Cron: 1AM)   │    │ (Сбор + фильтр)  │    │   (Дайджест)    │
└─────────────────┘    └──────────┬───────┘    └─────────┬───────┘
                                  │                       │
                            ┌─────▼──────┐         ┌──────▼──────┐
                            │ S3: data/  │         │ S3: reports/│
                            └────────────┘         └─────────────┘
```

### 2. Веб-интерфейс (lambda-web/)
FastAPI приложение для просмотра сгенерированных дайджестов с возможностью развертывания в AWS Lambda.

## 🚀 Быстрый старт

### AWS развертывание через Terraform

Проект использует Terraform для автоматизированного развертывания всей инфраструктуры AWS:
- Lambda функции для сбора и обработки данных
- S3 bucket для хранения данных и отчетов
- EventBridge для автоматического запуска по расписанию
- API Gateway для веб-интерфейса (опционально)
- CloudWatch для логов и мониторинга

```bash
# Развертывание всей инфраструктуры
cd terraform
terraform init
terraform apply
```

**Важно:** Перед развертыванием необходимо настроить backend для хранения Terraform state в S3. Подробные инструкции по настройке и развертыванию: [terraform/README.md](terraform/README.md)

## ⚙️ Настройка API ключей

### Reddit API
1. Перейдите на https://www.reddit.com/prefs/apps
2. Создайте новое приложение типа "script"
3. Скопируйте `client_id` и `client_secret`

### OpenAI API
1. Зарегистрируйтесь на https://platform.openai.com/
2. Создайте API ключ в разделе API Keys

### Переменные окружения
```bash
# Reddit API
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=ai-digest-script/0.1

# OpenAI API
OPENAI_API_KEY=your_openai_api_key

# Конфигурация
REDDIT_SUBREDDITS=ChatGPT,OpenAI,ClaudeAI,Bard,GeminiAI,DeepSeek,grok
# AWS
S3_BUCKET_NAME=your-bucket
```

## 📊 Примерная стоимость AWS

**Ежемесячно:**
- Lambda функции: ~$0.50
- S3 хранилище: ~$0.10
- CloudWatch логи: ~$0.05
- OpenAI API: 0 (free tokens https://help.openai.com/en/articles/10306912-sharing-feedback-evaluation-and-fine-tuning-data-and-api-inputs-and-outputs-with-openai)

- API Gateway (веб): ~$0.01

**Итого: менее $1/месяц**


## 📁 Структура проекта

```
reddit_script/
├── terraform/               # Terraform конфигурация
│   ├── main.tf             # Основная конфигурация
│   ├── variables.tf        # Переменные
│   └── README.md           # Инструкции по развертыванию
├── lambda-cron/             # AWS Lambda cron функции
│   ├── lambda_collect/      # Функция сбора постов
│   ├── lambda_summarize/    # Функция суммаризации
│   └── build.sh            # Сборка Lambda пакетов (опционально)
├── lambda-web/              # Веб-интерфейс
│   ├── src/                # FastAPI приложение
│   └── templates/          # HTML шаблоны
└── README.md               # Этот файл
```

## 🔍 Мониторинг

### AWS CloudWatch

После развертывания через Terraform, команды мониторинга будут выведены в консоли в секции `useful_commands`.

Terraform автоматически выводит полезные команды для:
- Тестирования Lambda функций
- Просмотра логов CloudWatch
- Работы с S3 bucket
- Ручного запуска процесса сбора

Используйте `terraform output useful_commands` для получения актуальных команд с правильными именами ресурсов.

### S3 структура данных
- `s3://bucket/data/posts_YYYY-MM-DD.json` - отфильтрованные посты
- `s3://bucket/data/all_posts_YYYY-MM-DD.json` - все собранные посты
- `s3://bucket/reports/digest_YYYY-MM-DD.md` - сгенерированные дайджесты


### Языковые требования
- **Код**: английские имена переменных и функций
- **Комментарии и документация**: русский язык
- **Пользовательский интерфейс**: русский язык
- **Дайджесты**: русский язык

## 📖 Документация

- [terraform/README.md](terraform/README.md) - Инструкции по развертыванию инфраструктуры AWS
- [lambda-cron/README.md](lambda-cron/README.md) - AWS Lambda cron функции
- [lambda-web/README.md](lambda-web/README.md) - Развертывание веб-интерфейса

## 📄 Лицензия

MIT License - используйте свободно для личных и коммерческих проектов.