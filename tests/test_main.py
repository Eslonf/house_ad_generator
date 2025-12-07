from fastapi.testclient import TestClient
import pytest

from app.main import app 

# --- Подготовка к тестам ---
# Создаем "виртуального клиента", который будет отправлять запросы к приложению.
client = TestClient(app)

# --- Тест-кейс №1 ---
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


# --- Тест-кейс №2 ---
def test_submit_image_successfully(mocker):
    """
    Тест проверяет успешную отправку изображения и постановку задачи в очередь.
    'mocker' - это специальный аргумент от pytest-mock для создания "моков".
    """
    # 1. Подготовка "мока":
    # Мы "подменяем" настоящую, тяжелую ML-функцию на заглушку.
    mocker.patch(
        'app.main.generate_ad_from_image', 
        return_value={"status": "mocked_ok"}
    )

    # 2. Действие:
    # Имитируем отправку файла, как это делает браузер.
    with open("tests/assets/test_image.png", "rb") as f:
        response = client.post(
            "/generate-ad",
            data={"style": "brief"},
            files={"image": ("test_image.png", f, "image/png")}
        )

    # 3. Проверки (Asserts):
    # Утверждаем, что сервер ответил кодом 202 (Accepted), 
    # что означает "задача принята в обработку".
    assert response.status_code == 202
    
    # Утверждаем, что в JSON-ответе есть ключ "task_id".
    data = response.json()
    assert "task_id" in data