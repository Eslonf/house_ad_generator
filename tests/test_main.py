from fastapi.testclient import TestClient
import pytest

from app.main import app 

# --- Подготовка к тестам ---
# Создаем "виртуального клиента", который будет отправлять запросы к приложению.
client = TestClient(app)

def test_read_main_page():
    """
    Тест проверяет, что главная страница ("/") успешно загружается.
    """
    # 1. Действие:
    # Отправляем GET-запрос на главную страницу.
    response = client.get("/")
    
    # 2. Проверка (Assert):
    # Утверждаем, что сервер ответил кодом 200 (OK).
    assert response.status_code == 200
    
    # 3. Проверка содержимого:
    assert "Генератор объявлений" in response.text