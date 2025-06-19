import json
import os
from typing import Any

import openai
from openai import OpenAI
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from utils import download_from_s3, format_date_for_digest, upload_to_s3


def prepare_prompt_data(
    posts: list[dict[str, Any]], formatted_date_for_digest: str
) -> dict[str, Any]:
    """
    Подготавливает данные для отправки в API с логикой группировки.

    Args:
        posts: Список отфильтрованных постов
        formatted_date_for_digest: Дата в формате DD-MM-YYYY для использования в заголовке

    Returns:
        Dict: Данные для промпта
    """
    posts_by_subreddit = {}

    for post in posts:
        subreddit = post["subreddit"]
        if subreddit not in posts_by_subreddit:
            posts_by_subreddit[subreddit] = []

        posts_by_subreddit[subreddit].append(
            {
                "title": post["title"],
                "score": post["score"],
                "num_comments": post["num_comments"],
                "permalink": post["permalink"],
                "selftext": post["selftext"][:500] if post["selftext"] else "",
                "author": post["author"],
            }
        )

    # Разделяем сабреддиты по количеству постов
    major_subreddits = {k: v for k, v in posts_by_subreddit.items() if len(v) >= 5}
    minor_subreddits = {k: v for k, v in posts_by_subreddit.items() if len(v) < 5}

    return {
        "major_subreddits": major_subreddits,
        "minor_subreddits": minor_subreddits,
        "instructions": (
            "Сделай обзор полученного списка постов, исключи при этом юмористические посты, "
            "мемы и картинки видеоролики. Сделай упор на технические публикации и описания "
            "пользовательского опыта.\n\n"
            "ЛОГИКА ГРУППИРОВКИ:\n"
            "1. Для сабреддитов с 5 и более постами: создай отдельные секции, выведи до 10 наиболее популярных постов\n"
            "2. Для сабреддитов с менее чем 5 постами: объедини их в общий раздел 'Прочие сабреддиты'\n\n"
            "ОБЯЗАТЕЛЬНО добавляй ссылки на посты. Используй формат:\n\n"
            f"# Дайджест Reddit • {formatted_date_for_digest}\\n\\n"
            "## r/[Subreddit] (для крупных сабреддитов)\n"
            "### ТОП-10\n"
            "1. **[Заголовок]** — краткое описание (👍 [score] | 💬 [comments]) [🔗 Ссылка](permalink)\n"
            "...\n\n"
            "## Прочие сабреддиты (для мелких сабреддитов)\n"
            "### r/[Subreddit]\n"
            "1. **[Заголовок]** — краткое описание (👍 [score] | 💬 [comments]) [🔗 Ссылка](permalink)\n"
            "...\n\n"
            "ВАЖНО: Для каждого поста используй точную ссылку из поля 'permalink' в формате [🔗 Ссылка](permalink_url). "
            "НЕ добавляй раздел с трендами - он будет добавлен отдельно."
        ),
    }


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type(openai.APIError)
    | retry_if_exception_type(openai.APITimeoutError)
    | retry_if_exception_type(openai.RateLimitError),
)
def call_openai_api_for_top_posts(data: dict[str, Any], api_key: str) -> str:
    """
    Отправляет отфильтрованные данные в OpenAI API для генерации топ-постов.

    Args:
        data: Данные для обработки
        api_key: API ключ OpenAI

    Returns:
        str: Сгенерированный обзор топ-постов
    """
    client = OpenAI(api_key=api_key)

    # Формируем данные для анализа
    analysis_data = {
        "major_subreddits": data["major_subreddits"],
        "minor_subreddits": data["minor_subreddits"],
    }

    prompt = f"{data['instructions']}\n\nДанные для анализа:\n{json.dumps(analysis_data, ensure_ascii=False, indent=2)}"

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            temperature=0.15,
            top_p=1.0,
            presence_penalty=0,
            frequency_penalty=0.1,
            seed=42,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=8000,
        )

        return response.choices[0].message.content

    except (openai.APIError, openai.APITimeoutError, openai.RateLimitError) as e:
        print(f"Ошибка OpenAI API при генерации топ-постов: {e}. Повторная попытка...")
        raise
    except Exception as e:
        print(f"Неизвестная ошибка при вызове OpenAI API для топ-постов: {e}")
        raise


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type(openai.APIError)
    | retry_if_exception_type(openai.APITimeoutError)
    | retry_if_exception_type(openai.RateLimitError),
)
def call_openai_api_for_trends(all_posts: list[dict[str, Any]], api_key: str) -> str:
    """
    Отправляет все посты в OpenAI API для анализа трендов.

    Args:
        all_posts: Все собранные посты
        api_key: API ключ OpenAI

    Returns:
        str: Анализ трендов
    """
    client = OpenAI(api_key=api_key)

    # Подготавливаем данные для анализа трендов - только заголовки и основная информация
    posts_for_trends = []
    for post in all_posts:
        posts_for_trends.append(
            {
                "title": post["title"],
                "subreddit": post["subreddit"],
                "score": post["score"],
                "num_comments": post["num_comments"],
                "selftext": post["selftext"][:200]
                if post["selftext"]
                else "",  # Укороченный текст
            }
        )

    prompt = (
        "Проанализируй все представленные посты из Reddit сабреддитов ChatGPT, OpenAI, ClaudeAI, Bard, GeminiAI, DeepSeek и grok. "
        "Найди 5 самых важных и популярных трендов в обсуждениях. "
        "Исключи юмористические посты и мемы. "
        "Сосредоточься на технических темах, пользовательском опыте и новых возможностях ИИ. "
        "Каждый тренд описывай не более чем в 3 предложения - кратко и емко. "
        "Формат ответа:\n\n"
        "#### Общие тренды\n"
        "* **[Название тренда]** — краткое описание в 1-3 предложения. Примерное количество постов: [число]\n"
        "* **[Название тренда]** — краткое описание в 1-3 предложения. Примерное количество постов: [число]\n"
        "...\n\n"
        f"Данные для анализа:\n{json.dumps(posts_for_trends, ensure_ascii=False, indent=2)}"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            temperature=0.15,
            top_p=1.0,
            presence_penalty=0,
            frequency_penalty=0.1,
            seed=42,
            messages=[{"role": "user", "content": prompt}],
            max_completion_tokens=8000,
        )

        return response.choices[0].message.content

    except (openai.APIError, openai.APITimeoutError, openai.RateLimitError) as e:
        print(f"Ошибка OpenAI API при анализе трендов: {e}. Повторная попытка...")
        raise
    except Exception as e:
        print(f"Неизвестная ошибка при вызове OpenAI API для трендов: {e}")
        raise


def generate_digest(date_str: str, filtered_posts_s3_key: str, all_posts_s3_key: str) -> dict[str, Any]:
    """
    Генерирует дайджест из собранных постов.
    
    Args:
        date_str: Дата в формате YYYY-MM-DD
        filtered_posts_s3_key: Ключ S3 с отфильтрованными постами
        all_posts_s3_key: Ключ S3 с всеми постами
        
    Returns:
        dict: Результат генерации дайджеста
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY не найден в переменных окружения")

    # Загружаем отфильтрованные посты для топ-10
    try:
        filtered_data = download_from_s3(filtered_posts_s3_key)
        filtered_posts = filtered_data["posts"]
        print(f"Загружено {len(filtered_posts)} отфильтрованных постов из S3")
    except Exception as e:
        raise Exception(f"Не удалось загрузить отфильтрованные данные: {e}")

    # Загружаем все посты для анализа трендов
    try:
        all_data = download_from_s3(all_posts_s3_key)
        all_posts = all_data["posts"]
        print(f"Загружено {len(all_posts)} всех постов для анализа трендов")
    except Exception as e:
        raise Exception(f"Не удалось загрузить все данные: {e}")

    if not filtered_posts:
        raise Exception("Нет отфильтрованных постов для обработки")

    # Преобразуем дату в формат DD-MM-YYYY для дайджеста
    formatted_date = format_date_for_digest(date_str)
    prompt_data = prepare_prompt_data(filtered_posts, formatted_date)

    print("Генерация топ-постов...")
    try:
        top_posts_digest = call_openai_api_for_top_posts(prompt_data, api_key)
        print("Топ-посты успешно сгенерированы")
    except Exception as e:
        raise Exception(f"Не удалось сгенерировать топ-посты: {e}")

    print("Анализ трендов...")
    try:
        trends_analysis = call_openai_api_for_trends(all_posts, api_key)
        print("Анализ трендов завершен")
    except Exception as e:
        raise Exception(f"Не удалось проанализировать тренды: {e}")

    # Объединяем результаты
    digest = top_posts_digest + "\n\n---\n\n" + trends_analysis

    # Сохраняем дайджест в S3
    report_s3_key = f"reports/digest_{date_str}.md"
    success = upload_to_s3(digest, report_s3_key)
    
    if not success:
        raise Exception(f"Не удалось загрузить дайджест в S3: {report_s3_key}")

    print(f"✅ Дайджест сохранен в S3: {report_s3_key}")
    print(f"Размер дайджеста: {len(digest)} символов")

    return {
        "status": "success",
        "date": date_str,
        "digest_s3_key": report_s3_key,
        "digest_size": len(digest),
        "total_filtered_posts": len(filtered_posts),
        "total_all_posts": len(all_posts)
    }