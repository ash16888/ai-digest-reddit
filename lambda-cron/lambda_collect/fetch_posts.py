import os
import sys
from datetime import datetime
from typing import Any

import praw
import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from utils import (
    get_berlin_date_string,
    get_yesterday_berlin,
    upload_to_s3,
)


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type(praw.exceptions.APIException)
    | retry_if_exception_type(requests.exceptions.RequestException),
)
def fetch_subreddit_posts(
    reddit: praw.Reddit, subreddit_name: str, start_time: datetime, end_time: datetime
) -> list[dict[str, Any]]:
    """
    Получает посты из указанного сабреддита за определенный период.

    Args:
        reddit: Объект PRAW Reddit
        subreddit_name: Название сабреддита
        start_time: Начало периода (UTC)
        end_time: Конец периода (UTC)

    Returns:
        List: Список постов с необходимыми полями
    """
    subreddit = reddit.subreddit(subreddit_name)
    posts = []

    start_timestamp = int(start_time.timestamp())
    end_timestamp = int(end_time.timestamp())

    try:
        processed_count = 0
        for submission in subreddit.new(limit=1000):  # Ограничиваем до 1000 постов
            processed_count += 1
            if processed_count % 100 == 0:
                print(f"  Обработано {processed_count} постов...")

            created_utc = int(submission.created_utc)

            if created_utc < start_timestamp:
                break

            if start_timestamp <= created_utc <= end_timestamp:
                post_data = {
                    "id": submission.id,
                    "created_utc": created_utc,
                    "title": submission.title,
                    "selftext": submission.selftext,
                    "score": submission.score,
                    "num_comments": submission.num_comments,
                    "permalink": f"https://reddit.com{submission.permalink}",
                    "author": str(submission.author)
                    if submission.author
                    else "[deleted]",
                    "link_flair_text": submission.link_flair_text,
                    "subreddit": subreddit_name,
                    "url": submission.url,
                    "post_hint": getattr(submission, "post_hint", None),
                }
                posts.append(post_data)

    except (praw.exceptions.APIException, requests.exceptions.RequestException) as e:
        print(
            f"Ошибка API при получении постов из r/{subreddit_name}: {e}. Повторная попытка..."
        )
        raise  # tenacity перехватит и повторит
    except Exception as e:
        print(f"Неизвестная ошибка при получении постов из r/{subreddit_name}: {e}")
        return []

    return posts


def collect_posts() -> dict[str, Any]:
    """
    Основная функция для сбора постов за вчерашний день.
    
    Returns:
        dict: Результат выполнения с информацией о собранных постах
    """
    # Получаем переменные окружения
    client_id = os.environ.get("REDDIT_CLIENT_ID")
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
    user_agent = os.environ.get("REDDIT_USER_AGENT", "digest-script/0.1")
    subreddits_str = os.environ.get("REDDIT_SUBREDDITS")

    if not client_id or not client_secret:
        raise ValueError("REDDIT_CLIENT_ID или REDDIT_CLIENT_SECRET не найдены")

    # Парсим список сабреддитов из строки
    subreddits = [sub.strip() for sub in subreddits_str.split(",") if sub.strip()]
    if not subreddits:
        raise ValueError("Список сабреддитов пуст")

    try:
        reddit = praw.Reddit(
            client_id=client_id, client_secret=client_secret, user_agent=user_agent
        )
        reddit.read_only = True

        print("Успешно подключено к Reddit API")

    except Exception as e:
        raise Exception(f"Ошибка подключения к Reddit API: {e}")

    start_time, end_time = get_yesterday_berlin()
    date_str = get_berlin_date_string()

    print(f"Сбор постов за {date_str}")
    print(f"Период: {start_time} - {end_time} UTC")
    print(f"Мониторим сабреддиты: {', '.join(subreddits)}")

    all_posts = []

    for subreddit_name in subreddits:
        print(f"\nСбор постов из r/{subreddit_name}...")
        posts = fetch_subreddit_posts(reddit, subreddit_name, start_time, end_time)
        print(f"Найдено {len(posts)} постов")
        all_posts.extend(posts)

    print(f"\nВсего собрано постов: {len(all_posts)}")

    # Подготавливаем данные для сохранения
    data_to_save = {
        "date": date_str,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "total_posts": len(all_posts),
        "posts": all_posts,
    }

    # Сохраняем в S3
    s3_key = f"data/all_posts_{date_str}.json"
    success = upload_to_s3(data_to_save, s3_key)
    
    if not success:
        raise Exception(f"Не удалось загрузить данные в S3: {s3_key}")

    return {
        "status": "success",
        "date": date_str,
        "total_posts": len(all_posts),
        "s3_key": s3_key,
        "subreddits": subreddits
    }