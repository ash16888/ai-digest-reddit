import json
import os
from typing import Any, Dict

import boto3

from fetch_posts import collect_posts
from filter_posts import filter_collected_posts
from utils import get_berlin_date_string


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler для сбора и фильтрации постов Reddit.
    
    Args:
        event: Событие Lambda (от EventBridge)
        context: Контекст Lambda
        
    Returns:
        Dict: Результат выполнения
    """
    print("🚀 Запуск Lambda функции сбора и фильтрации постов")
    print(f"📋 Event: {json.dumps(event, default=str, indent=2)}")
    
    # Проверяем, что это не циклический вызов
    if event.get("source") == "aws.lambda":
        print("⚠️  Обнаружен циклический вызов от другой Lambda функции, игнорируем")
        return {
            "statusCode": 200,
            "body": {"status": "skipped", "reason": "Циклический вызов от Lambda"}
        }
    
    try:
        # Получаем дату для обработки
        date_str = get_berlin_date_string()
        print(f"📅 Обработка данных за {date_str}")
        
        # Проверяем, не обрабатывались ли уже посты за сегодня
        from utils import check_s3_key_exists
        all_posts_key = f"data/all_posts_{date_str}.json"
        
        if check_s3_key_exists(all_posts_key):
            print(f"⚠️  Данные за {date_str} уже обработаны, пропускаем выполнение")
            return {
                "statusCode": 200,
                "body": {
                    "status": "skipped", 
                    "reason": f"Данные за {date_str} уже существуют",
                    "date": date_str
                }
            }
        
        # Этап 1: Сбор постов
        print("\n📥 Этап 1: Сбор постов из Reddit")
        collect_result = collect_posts()
        print(f"✅ Сбор завершен: {collect_result}")
        
        # Этап 2: Фильтрация постов
        print("\n🔍 Этап 2: Фильтрация постов")
        filter_result = filter_collected_posts(date_str)
        print(f"✅ Фильтрация завершена: {filter_result}")
        
        # Этап 3: Запуск Lambda функции суммаризации
        print("\n📊 Этап 3: Запуск суммаризации")
        summarize_function_name = os.environ.get("SUMMARIZE_FUNCTION_NAME")
        
        if summarize_function_name:
            try:
                lambda_client = boto3.client("lambda")
                
                # Подготавливаем payload для функции суммаризации
                summarize_payload = {
                    "date": date_str,
                    "filtered_posts_s3_key": filter_result["filtered_posts_s3_key"],
                    "all_posts_s3_key": filter_result["all_posts_s3_key"]
                }
                
                # Асинхронный вызов функции суммаризации
                response = lambda_client.invoke(
                    FunctionName=summarize_function_name,
                    InvocationType='Event',  # Асинхронный вызов
                    Payload=json.dumps(summarize_payload)
                )
                
                print(f"✅ Lambda функция суммаризации запущена: {summarize_function_name}")
                print(f"Response StatusCode: {response['StatusCode']}")
                
            except Exception as e:
                print(f"⚠️  Ошибка при запуске функции суммаризации: {e}")
                # Не прерываем выполнение, так как основная задача выполнена
        else:
            print("⚠️  SUMMARIZE_FUNCTION_NAME не настроен, пропускаем запуск суммаризации")
        
        # Формируем итоговый результат
        result = {
            "statusCode": 200,
            "body": {
                "status": "success",
                "message": "Сбор и фильтрация постов завершены успешно",
                "date": date_str,
                "collect_result": collect_result,
                "filter_result": filter_result,
                "summarize_triggered": bool(summarize_function_name)
            }
        }
        
        print(f"🎉 Обработка завершена успешно за {date_str}")
        return result
        
    except Exception as e:
        error_message = f"❌ Ошибка при обработке: {str(e)}"
        print(error_message)
        
        return {
            "statusCode": 500,
            "body": {
                "status": "error",
                "message": error_message,
                "date": get_berlin_date_string()
            }
        }