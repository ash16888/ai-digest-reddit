import json
import os
from datetime import datetime

import boto3


def upload_to_s3(content: str, s3_key: str, bucket_name: str = None, content_type: str = "text/markdown") -> bool:
    """
    Загружает текстовый контент в S3.

    Args:
        content: Текстовый контент для загрузки
        s3_key: Ключ в S3
        bucket_name: Имя бакета (по умолчанию из переменной окружения)
        content_type: MIME тип контента

    Returns:
        bool: True если успешно
    """
    if bucket_name is None:
        bucket_name = os.environ.get("S3_BUCKET_NAME")
    
    if not bucket_name:
        raise ValueError("S3_BUCKET_NAME не найден в переменных окружения")

    try:
        s3_client = boto3.client("s3")
        
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=content.encode('utf-8'),
            ContentType=content_type
        )
        
        print(f"✅ Контент успешно загружен в s3://{bucket_name}/{s3_key}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка загрузки в S3: {e}")
        return False


def download_from_s3(s3_key: str, bucket_name: str = None) -> any:
    """
    Скачивает и парсит JSON данные из S3.

    Args:
        s3_key: Ключ в S3
        bucket_name: Имя бакета (по умолчанию из переменной окружения)

    Returns:
        any: Загруженные данные
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


def format_date_for_digest(date_str: str) -> str:
    """
    Преобразует дату из формата YYYY-MM-DD в DD-MM-YYYY.

    Args:
        date_str: Дата в формате YYYY-MM-DD

    Returns:
        str: Дата в формате DD-MM-YYYY
    """
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%d-%m-%Y")
    except ValueError:
        # Если формат не распознан, возвращаем как есть
        return date_str


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