import json
from typing import Any, Dict

from summarize import generate_digest


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler для генерации дайджеста Reddit постов.
    
    Args:
        event: Событие Lambda (от другой Lambda или тест)
        context: Контекст Lambda
        
    Returns:
        Dict: Результат выполнения
    """
    print("📊 Запуск Lambda функции генерации дайджеста")
    print(f"Получено событие: {json.dumps(event, ensure_ascii=False, indent=2)}")
    
    try:
        # Извлекаем параметры из события
        date_str = event.get("date")
        filtered_posts_s3_key = event.get("filtered_posts_s3_key")
        all_posts_s3_key = event.get("all_posts_s3_key")
        
        if not date_str:
            raise ValueError("Параметр 'date' не найден в событии")
        if not filtered_posts_s3_key:
            raise ValueError("Параметр 'filtered_posts_s3_key' не найден в событии")
        if not all_posts_s3_key:
            raise ValueError("Параметр 'all_posts_s3_key' не найден в событии")
        
        print(f"📅 Генерация дайджеста за {date_str}")
        print(f"📄 Отфильтрованные посты: {filtered_posts_s3_key}")
        print(f"📄 Все посты: {all_posts_s3_key}")
        
        # Генерируем дайджест
        result = generate_digest(date_str, filtered_posts_s3_key, all_posts_s3_key)
        
        # Формируем успешный ответ
        response = {
            "statusCode": 200,
            "body": {
                "status": "success",
                "message": "Дайджест успешно сгенерирован",
                "result": result
            }
        }
        
        print(f"🎉 Генерация дайджеста завершена успешно: {result}")
        return response
        
    except Exception as e:
        error_message = f"❌ Ошибка при генерации дайджеста: {str(e)}"
        print(error_message)
        
        return {
            "statusCode": 500,
            "body": {
                "status": "error",
                "message": error_message,
                "event": event
            }
        }