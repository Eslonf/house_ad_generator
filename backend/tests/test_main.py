from fastapi.testclient import TestClient
import pytest
from app.main import app 

# Инициализируем тестовый клиент FastAPI
client = TestClient(app)

def test_submit_image_successfully(mocker):
    """
    ПРОВЕРКА 'СЧАСТЛИВОГО ПУТИ': Успешная отправка картинки.
    """
    # Мокаем (подменяем) ML-функцию, чтобы не запускать нейросети во время тестов
    mocker.patch('app.main.generate_ad_from_image', return_value={"status": "mocked_ok"})
    
    with open("tests/assets/test_image.png", "rb") as f:
        # Имитируем отправку формы (изображение + стиль)
        response = client.post(
            "/api/generate-ad",
            data={"style": "brief"},
            files={"image": ("test_image.png", f, "image/png")}
        )
    # Ожидаем, что сервер принял задачу (202) и вернул task_id
    assert response.status_code == 202
    assert "task_id" in response.json()

def test_submit_wrong_file_type():
    """
    НЕГАТИВНЫЙ ТЕСТ: Попытка отправить текстовый файл вместо картинки.
    """
    with open("tests/assets/fake_image.txt", "rb") as f:
        response = client.post(
            "/api/generate-ad",
            data={"style": "brief"},
            files={"image": ("fake_image.txt", f, "text/plain")}
        )
    # Ожидаем, что сервер отвергнет запрос (400)
    assert response.status_code == 400

def test_get_result_not_found():
    """
    НЕГАТИВНЫЙ ТЕСТ: Запрос несуществующего результата.
    Проверяем логику опроса: если ID нет, сервер должен ответить 'processing' (202).
    """
    response = client.get("/api/results/fake-uuid-1234")
    assert response.status_code == 202
    assert response.json()["status"] == "processing"

def test_task_execution_failure(mocker):
    """
    ТЕСТ ОБРАБОТКИ ОШИБОК: Падение ML-модели.
    Проверяет, что если воркер упал, клиент корректно получит ошибку 500, а не зависнет.
    """
    # Заставляем мок-функцию ВЫБРОСИТЬ исключение
    mocker.patch('app.main.generate_ad_from_image', side_effect=Exception("ML Model crashed!"))
    
    # 1. Отправляем задачу
    with open("tests/assets/test_image.png", "rb") as f:
        submit_res = client.post(
            "/api/generate-ad",
            data={"style": "brief"},
            files={"image": ("test_image.png", f, "image/png")}
        )
    task_id = submit_res.json()["task_id"]

    # 2. Имитируем работу воркера, сохраняя ошибку в словарь (как это сделал бы реальный воркер)
    from app.state import TASK_RESULTS
    TASK_RESULTS[task_id] = {"status": "failed", "error": "ML Model crashed!"}

    # 3. Опрашиваем результат
    response = client.get(f"/api/results/{task_id}")
    
    # Ожидаем 500 (Internal Server Error) и текст нашей ошибки
    assert response.status_code == 500
    assert "ML Model crashed!" in response.json()["detail"]