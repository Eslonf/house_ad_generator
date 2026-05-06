import uuid
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, status
from fastapi.responses import JSONResponse
from app.state import TASK_QUEUE, TASK_RESULTS

router = APIRouter()

@router.post("/generate-ad")
async def generate_ad_task_endpoint(
    style: str = Form(...),
    image: UploadFile = File(...)
):
    """
    Эндпоинт для загрузки изображения.
    Он не выполняет обработку сам, а лишь генерирует ID, 
    кладет задачу в очередь и МГНОВЕННО возвращает этот ID клиенту.
    """
    # Проверка: является ли загруженный файл изображением
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Недопустимый тип файла.")

    # Генерируем уникальный ID для отслеживания задачи
    task_id = str(uuid.uuid4())
    
    # Читаем файл в память
    image_bytes = await image.read()

    # Помещаем данные в глобальную очередь, чтобы воркер их забрал
    await TASK_QUEUE.put({"task_id": task_id, "image_bytes": image_bytes, "style": style})
    
    # Возвращаем клиенту статус 202 (Принято в обработку) и ID задачи
    return JSONResponse(status_code=202, content={"task_id": task_id})

@router.get("/results/{task_id}")
async def get_task_result_endpoint(task_id: str):
    """
    Эндпоинт для опроса результата (Polling).
    Фронтенд периодически стучится сюда с task_id, чтобы узнать, готов ли текст.
    """
    # Ищем результат в глобальном словаре
    result = TASK_RESULTS.get(task_id)

    if result is None:
        # Если результата нет, значит воркер еще не закончил. Отвечаем 202.
        return JSONResponse(status_code=202, content={"status": "processing"})
    
    # Если результат есть, забираем его и удаляем из словаря (очищаем память)
    final_result = TASK_RESULTS.pop(task_id)

    # Проверяем, не завершилась ли задача с ошибкой внутри воркера
    if final_result["status"] == "failed":
        # Если ML-модель упала, возвращаем статус 500 и текст ошибки
        raise HTTPException(status_code=500, detail=final_result.get("error"))

    # Если всё хорошо, возвращаем 200 OK и сгенерированные данные
    return JSONResponse(status_code=200, content=final_result["data"])