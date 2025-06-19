# CLAUDE.md

Этот файл предоставляет руководство для Claude Code (claude.ai/code) при работе с кодом в данном репозитории.

## Обзор проекта

Reddit AI Digest — это serverless система, которая автоматически генерирует ежедневные дайджесты AI-новостей из постов Reddit. Состоит из двух основных компонентов:
- **lambda-cron/**: AWS Lambda функции для автоматического сбора данных и AI-суммаризации
- **lambda-web/**: FastAPI веб-приложение для просмотра сгенерированных дайджестов

## Основные команды

### Сборка и развертывание Lambda функций
```bash
# Сборка Lambda пакетов для сбора данных
cd lambda-cron
./build.sh

# Развертывание в AWS через Terraform
cd ../terraform
terraform init
terraform apply

# Сборка Lambda пакета веб-приложения
cd ../lambda-web
./build_lambda.sh
```

### Локальная разработка (Веб-приложение)
```bash
cd lambda-web
pip install -r requirements.txt
python -m uvicorn src.web_app:app --reload
```

### Мониторинг и тестирование
```bash
# После развертывания через Terraform используйте команды из вывода:
terraform output useful_commands

# Это выведет актуальные команды для:
# - Тестирования Lambda функций
# - Просмотра логов CloudWatch
# - Работы с S3 bucket
# - Ручного запуска процесса
```

## Архитектура

### Поток данных
1. **EventBridge** запускается ежедневно в 1:00 UTC
2. **Lambda Collect** собирает посты из 7 AI-сабреддитов, фильтрует мемы/низкокачественный контент
3. **Lambda Summarize** использует OpenAI API для генерации дайджестов на русском языке
4. **FastAPI Web App** предоставляет пользовательский интерфейс для просмотра дайджестов

### Структура хранения
- `s3://ai-reddit-digest/data/` - Сырые и отфильтрованные посты Reddit (JSON)
- `s3://ai-reddit-digest/reports/` - Сгенерированные дайджесты (Markdown)

## Ключевая конфигурация

### Необходимые переменные окружения
- `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` - Учетные данные Reddit API
- `OPENAI_API_KEY` - API ключ OpenAI для генерации дайджестов
- `REDDIT_SUBREDDITS` - Список сабреддитов для мониторинга через запятую

### Отслеживаемые сабреддиты
ChatGPT, OpenAI, ClaudeAI, Bard, GeminiAI, DeepSeek, grok

## Архитектура кода

### Lambda функции
- **lambda_collect/lambda_function.py**: Главная точка входа для сбора данных
- **lambda_summarize/lambda_function.py**: AI генерация дайджестов с использованием OpenAI
- Обе используют **collect.py** и **summarize.py** для основной логики

### Веб-приложение
- **lambda_handler.py**: Точка входа AWS Lambda с использованием Mangum адаптера
- **src/web_app.py**: FastAPI приложение с русской локализацией
- **templates/**: Jinja2 HTML шаблоны для веб-интерфейса

### Языковые требования
- Код: Английские имена переменных/функций
- Комментарии/Документация: Русский язык
- Пользовательский интерфейс: Русский язык
- Сгенерированные дайджесты: Русский язык

## Заметки по разработке

- Lambda пакеты оптимизированы по размеру (удаляются __pycache__, tests, ненужные dist-info)
- Веб-приложение использует Mangum для развертывания в AWS Lambda с сохранением совместимости с FastAPI
- Система обрабатывает ~100-200 постов ежедневно, генерируя структурированные дайджесты с категориями
- Оптимизированная по стоимости serverless архитектура (<$1/месяц операционные расходы)

You run in an environment where ast-grep is available; whenever a search requires syntax-aware or structural matching, default to ast-grep --lang python -p '<pattern>' (or set --lang appropriately) and avoid falling back to text-only tools like rg or grep unless I explicitly request a plain-text search.