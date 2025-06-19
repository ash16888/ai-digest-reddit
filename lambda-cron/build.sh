#!/bin/bash

# Скрипт сборки Lambda пакетов для Reddit дайджеста
set -e

echo "🔨 Начинаем сборку Lambda пакетов..."

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для логирования
log_info() {
    echo -e "${GREEN}ℹ️  $1${NC}"
}

log_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Проверяем наличие Python
if ! command -v python3 &> /dev/null; then
    log_error "Python3 не найден. Установите Python 3.12+"
    exit 1
fi

# Проверяем наличие pip
if ! command -v pip3 &> /dev/null; then
    log_error "pip3 не найден. Установите pip"
    exit 1
fi

# Проверяем наличие директорий
if [ ! -d "lambda_collect" ]; then
    log_error "Директория lambda_collect не найдена"
    exit 1
fi

if [ ! -d "lambda_summarize" ]; then
    log_error "Директория lambda_summarize не найдена"
    exit 1
fi

# Создаем временные директории для сборки
log_info "Создаем временные директории..."
rm -rf build_collect build_summarize
mkdir -p build_collect build_summarize

# Сборка Lambda функции для сбора постов
log_info "Сборка Lambda функции для сбора постов..."

# Копируем исходный код
cp lambda_collect/*.py build_collect/

# Устанавливаем зависимости
log_info "Устанавливаем зависимости для функции сбора..."
pip3 install -r lambda_collect/requirements.txt -t build_collect/

# Удаляем ненужные файлы для уменьшения размера
find build_collect/ -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find build_collect/ -type f -name "*.pyc" -delete 2>/dev/null || true
find build_collect/ -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
find build_collect/ -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true

# Создаем ZIP архив
log_info "Создаем ZIP архив для функции сбора..."
cd build_collect
zip -r ../lambda_collect.zip . -q
cd ..

log_info "✅ Lambda пакет для сбора создан: lambda_collect.zip ($(du -h lambda_collect.zip | cut -f1))"

# Сборка Lambda функции для суммаризации
log_info "Сборка Lambda функции для суммаризации..."

# Копируем исходный код
cp lambda_summarize/*.py build_summarize/

# Устанавливаем зависимости
log_info "Устанавливаем зависимости для функции суммаризации..."
pip3 install -r lambda_summarize/requirements.txt -t build_summarize/

# Удаляем ненужные файлы для уменьшения размера
find build_summarize/ -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find build_summarize/ -type f -name "*.pyc" -delete 2>/dev/null || true
find build_summarize/ -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
find build_summarize/ -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true

# Создаем ZIP архив
log_info "Создаем ZIP архив для функции суммаризации..."
cd build_summarize
zip -r ../lambda_summarize.zip . -q
cd ..

log_info "✅ Lambda пакет для суммаризации создан: lambda_summarize.zip ($(du -h lambda_summarize.zip | cut -f1))"

# Очищаем временные директории
log_info "Очищаем временные файлы..."
rm -rf build_collect build_summarize

echo ""
log_info "🎉 Сборка завершена успешно!"
echo ""
echo "Созданные пакеты:"
echo "📦 lambda_collect.zip   - Функция сбора и фильтрации постов"
echo "📦 lambda_summarize.zip - Функция генерации дайджеста"
echo ""
echo "Следующий шаг: используйте Terraform для развертывания (см. ../terraform/README.md)"