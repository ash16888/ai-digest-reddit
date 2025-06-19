import json
import os
from datetime import datetime, timedelta
from typing import Any

import boto3
import pytz


def get_yesterday_berlin() -> tuple[datetime, datetime]:
    """
    Возвращает начало и конец вчерашнего дня в timezone Europe/Berlin.

    Returns:
        tuple: (start_datetime, end_datetime) в UTC
    """
    berlin_tz = pytz.timezone("Europe/Berlin")
    now_berlin = datetime.now(berlin_tz)

    yesterday_berlin = now_berlin - timedelta(days=1)
    start_berlin = yesterday_berlin.replace(hour=0, minute=0, second=0, microsecond=0)
    end_berlin = yesterday_berlin.replace(
        hour=23, minute=59, second=59, microsecond=999999
    )

    start_utc = start_berlin.astimezone(pytz.UTC)
    end_utc = end_berlin.astimezone(pytz.UTC)

    return start_utc, end_utc


def get_berlin_date_string() -> str:
    """
    Возвращает вчерашнюю дату по берлинскому времени в формате YYYY-MM-DD.

    Returns:
        str: Вчерашняя дата в формате YYYY-MM-DD
    """
    berlin_tz = pytz.timezone("Europe/Berlin")
    now_berlin = datetime.now(berlin_tz)
    yesterday_berlin = now_berlin - timedelta(days=1)
    return yesterday_berlin.strftime("%Y-%m-%d")


def is_meme_post(post: dict[str, Any]) -> bool:
    """
    Определяет, является ли пост мемом или юмористическим контентом.

    Args:
        post: Словарь с данными поста

    Returns:
        bool: True если пост - мем/юмор
    """
    title_lower = (post.get("title") or "").lower()
    selftext_lower = (post.get("selftext") or "").lower()
    link_flair_text = (post.get("link_flair_text") or "").lower()

    meme_keywords = [
        "meme",
        "joke",
        "funny",
        "lol",
        "lmao",
        "rofl",
        "humor",
        "humour",
        "shitpost",
        "shit post",
        "memeing",
        "jk",
        "just kidding",
        "trolling",
    ]

    for keyword in meme_keywords:
        if keyword in title_lower or keyword in selftext_lower:
            return True

    if (
        "meme" in link_flair_text
        or "humor" in link_flair_text
        or "funny" in link_flair_text
    ):
        return True

    if post.get("post_hint") == "image":
        if any(
            ext in post.get("url", "").lower()
            for ext in [".gif", ".jpg", ".jpeg", ".png"]
        ):
            if len(selftext_lower) < 100:
                return True

    return False


def filter_posts(
    posts: list[dict[str, Any]], min_score: int = 30, min_comments: int = 30
) -> list[dict[str, Any]]:
    """
    Фильтрует посты по критериям популярности и исключает мемы.

    Args:
        posts: Список постов
        min_score: Минимальный score
        min_comments: Минимальное количество комментариев

    Returns:
        List: Отфильтрованные посты
    """
    filtered = []

    for post in posts:
        if (
            post.get("score", 0) >= min_score
            or post.get("num_comments", 0) >= min_comments
        ):
            if not is_meme_post(post):
                filtered.append(post)

    return filtered


def upload_to_s3(data: Any, s3_key: str, bucket_name: str = None) -> bool:
    """
    Загружает данные в S3 в формате JSON.

    Args:
        data: Данные для загрузки
        s3_key: Ключ в S3
        bucket_name: Имя бакета (по умолчанию из переменной окружения)

    Returns:
        bool: True если успешно
    """
    if bucket_name is None:
        bucket_name = os.environ.get("S3_BUCKET_NAME")
    
    if not bucket_name:
        raise ValueError("S3_BUCKET_NAME не найден в переменных окружения")

    try:
        s3_client = boto3.client("s3")
        
        json_content = json.dumps(data, ensure_ascii=False, indent=2)
        
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=json_content.encode('utf-8'),
            ContentType='application/json'
        )
        
        print(f"✅ Данные успешно загружены в s3://{bucket_name}/{s3_key}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка загрузки в S3: {e}")
        return False


def download_from_s3(s3_key: str, bucket_name: str = None) -> Any:
    """
    Скачивает и парсит JSON данные из S3.

    Args:
        s3_key: Ключ в S3
        bucket_name: Имя бакета (по умолчанию из переменной окружения)

    Returns:
        Any: Загруженные данные
    """
    if bucket_name is None:
        bucket_name = os.environ.get("S3_BUCKET_NAME")
    
    if not bucket_name:
        raise ValueError("S3_BUCKET_NAME не найден в переменных окружения")

    try:
        s3_client = boto3.client("s3")
        
        response = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
        content = response['Body'].read().decode('utf-8')
        
        return json.loads(content)
        
    except Exception as e:
        print(f"❌ Ошибка скачивания из S3: {e}")
        raise


def check_s3_key_exists(s3_key: str, bucket_name: str = None) -> bool:
    """
    Проверяет существование ключа в S3.

    Args:
        s3_key: Ключ в S3
        bucket_name: Имя бакета (по умолчанию из переменной окружения)

    Returns:
        bool: True если ключ существует
    """
    if bucket_name is None:
        bucket_name = os.environ.get("S3_BUCKET_NAME")
    
    if not bucket_name:
        raise ValueError("S3_BUCKET_NAME не найден в переменных окружения")

    try:
        s3_client = boto3.client("s3")
        s3_client.head_object(Bucket=bucket_name, Key=s3_key)
        return True
    except Exception as e:
        if "NoSuchKey" in str(e) or "404" in str(e):
            return False
        print(f"❌ Ошибка проверки ключа S3: {e}")
        return False