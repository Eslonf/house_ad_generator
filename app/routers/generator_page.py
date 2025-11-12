import uuid
from fastapi import APIRouter, Request, File, UploadFile, HTTPException, status, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.state import TASK_QUEUE, TASK_RESULTS

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Отдает главную HTML-страницу."""
    return templates.TemplateResponse("index.html", {"request": request})

@router.post("/generate-ad")
async def generate_ad_task_endpoint(
    style: str = Form(...),
    image: UploadFile = File(...)
):
    """
    МГНОВЕННО принимает задачу, кладет ее в очередь и возвращает ID задачи.
    """
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Недопустимый тип файла.")

    # Генерируем уникальный ID для нашей задачи
    task_id = str(uuid.uuid4())
    image_bytes = await image.read()

    # Создаем задачу и кладем ее в асинхронную очередь
    task = {"task_id": task_id, "image_bytes": image_bytes, "style": style}
    await TASK_QUEUE.put(task)

    # Сразу же возвращаем клиенту ID, по которому он будет проверять результат
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content={"task_id": task_id})

@router.get("/results/{task_id}")
async def get_task_result_endpoint(task_id: str):
    """
    Проверяет статус задачи. Если она готова - возвращает результат.
    Если в процессе - сообщает об этом.
    """
    result = TASK_RESULTS.get(task_id)

    if result is None:
        # Задача еще не обработана воркером
        return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content={"status": "processing"})
    
    # Удаляем результат после того, как отдали его
    final_result = TASK_RESULTS.pop(task_id)

    if final_result["status"] == "failed":
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=final_result.get("error"))

    return JSONResponse(status_code=status.HTTP_200_OK, content=final_result["data"])