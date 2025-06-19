# Reddit AI Digest - Web Interface

Веб-интерфейс для просмотра сгенерированных дайджестов Reddit AI Digest.

⚠️ **ВАЖНО**: Развертывание теперь выполняется через Terraform! См. [../terraform/README.md](../terraform/README.md)

## Локальная разработка

### Предварительные требования

1. **Python 3.12**
2. **Доступ к S3 bucket** с дайджестами

### Установка и запуск

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск приложения
export S3_BUCKET_NAME=ai-reddit-digest
python -m uvicorn src.web_app:app --reload
```

Приложение будет доступно по адресу http://localhost:8000

### Переменные окружения

- `S3_BUCKET_NAME` - имя S3 bucket с данными дайджестов (обязательная)
- `REDDIT_SUBREDDITS` - список отслеживаемых subreddit через запятую (опционально)

## Структура проекта

```
lambda-web/
├── lambda_handler.py      # Lambda обработчик для FastAPI
├── build_lambda.sh        # Скрипт сборки deployment package (опционально)
├── requirements.txt       # Python зависимости
├── src/                   # Исходный код FastAPI приложения
│   ├── web_app.py        # Основное приложение
│   ├── s3_storage.py     # Работа с S3
│   ├── templates/        # HTML шаблоны
│   └── static/           # CSS стили
└── README.md             # Этот файл
```

## Развертывание

Развертывание выполняется через Terraform:

```bash
cd ../terraform
terraform init
terraform apply
```

Подробные инструкции см. в [../terraform/README.md](../terraform/README.md)

## Основные функции

### Главная страница
Отображает последний дайджест с кратким обзором и ссылками на предыдущие.

### Архив дайджестов
Полный список всех доступных дайджестов с возможностью просмотра.

### Просмотр дайджеста
Полный текст дайджеста с форматированием Markdown.

### API endpoints
- `GET /` - главная страница
- `GET /archive` - архив дайджестов
- `GET /digest/{date}` - просмотр дайджеста
- `GET /api/digests` - JSON API

## Сборка Lambda пакета

Для локальной сборки Lambda пакета (опционально, Terraform делает это автоматически):

```bash
./build_lambda.sh
```

Это создаст файл `lambda_deployment.zip` с приложением и всеми зависимостями.

## Мониторинг

После развертывания через Terraform используйте:

```bash
# Получить URL веб-интерфейса
terraform output api_gateway_url

# Получить команды мониторинга
terraform output useful_commands
```

Команды включают инструкции для просмотра логов и тестирования API.