from typing import Any

from utils import download_from_s3, filter_posts, upload_to_s3


def filter_collected_posts(date_str: str) -> dict[str, Any]:
    """
    Фильтрует собранные посты по критериям популярности.
    
    Args:
        date_str: Дата в формате YYYY-MM-DD
        
    Returns:
        dict: Результат выполнения фильтрации
    """
    # Скачиваем все посты из S3
    all_posts_key = f"data/all_posts_{date_str}.json"
    
    try:
        data = download_from_s3(all_posts_key)
        all_posts = data["posts"]
        print(f"Загружено {len(all_posts)} постов из S3")
    except Exception as e:
        raise Exception(f"Не удалось загрузить данные из S3: {e}")

    # Фильтруем посты
    filtered_posts = filter_posts(all_posts)
    
    print(f"После фильтрации: {len(filtered_posts)} постов")
    print(f"Исключено мемов и неподходящего контента: {len(all_posts) - len(filtered_posts)} постов")

    # Подготавливаем данные для сохранения
    filtered_data = {
        "date": date_str,
        "start_time": data["start_time"],
        "end_time": data["end_time"],
        "total_posts_collected": len(all_posts),
        "total_posts_filtered": len(filtered_posts),
        "posts": filtered_posts,
    }

    # Сохраняем отфильтрованные данные в S3
    filtered_posts_key = f"data/posts_{date_str}.json"
    success = upload_to_s3(filtered_data, filtered_posts_key)
    
    if not success:
        raise Exception(f"Не удалось загрузить отфильтрованные данные в S3: {filtered_posts_key}")

    return {
        "status": "success",
        "date": date_str,
        "total_collected": len(all_posts),
        "total_filtered": len(filtered_posts),
        "filtered_posts_s3_key": filtered_posts_key,
        "all_posts_s3_key": all_posts_key
    }