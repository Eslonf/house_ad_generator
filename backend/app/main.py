import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.routers import generator_page
from app.ml_model.processing import generate_ad_from_image
from app.state import TASK_QUEUE, TASK_RESULTS

async def worker():
    """
    Фоновый воркер (Background Task).
    Бесконечно слушает очередь задач (TASK_QUEUE).
    Когда появляется задача, забирает её, вызывает ML-пайплайн и сохраняет результат.
    """
    print("Воркер запущен и готов к работе...")
    while True:
        # Ждем, пока в очереди появится задача
        task = await TASK_QUEUE.get()
        task_id = task["task_id"]
        print(f"Воркер взял в работу задачу: {task_id}")
        
        try:
            result = await asyncio.to_thread(
                generate_ad_from_image, 
                task["image_bytes"], 
                task["style"]
            )
            # Если всё прошло успешно, сохраняем результат
            TASK_RESULTS[task_id] = {"status": "completed", "data": result}
        except Exception as e:
            # Если ML-модель упала (нехватка памяти и т.д.), сохраняем ошибку
            print(f"Ошибка в воркере: {e}")
            TASK_RESULTS[task_id] = {"status": "failed", "error": str(e)}
        finally:
            # Сообщаем очереди, что задача обработана
            TASK_QUEUE.task_done()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan менеджер управляет жизненным циклом приложения (при старте и выключении).
    """
    asyncio.create_task(worker())
    yield

# Создаем экземпляр FastAPI
app = FastAPI(title="Генератор объявлений API", lifespan=lifespan)

# --- НАСТРОЙКА CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутер с нашими эндпоинтами, добавляя общий префикс /api
app.include_router(generator_page.router, prefix="/api")

# --- РАЗДАЧА ФРОНТЕНДА ---
dist_path = os.path.join(os.getcwd(), "..", "frontend", "dist")

if os.path.exists(dist_path):
    # Раздаем скомпилированные JS/CSS файлы
    app.mount("/assets", StaticFiles(directory=os.path.join(dist_path, "assets")), name="assets")
    
    # Все остальные запросы (например, обновление страницы) перенаправляем на index.html Vue
    @app.get("/{catchall:path}", include_in_schema=False)
    async def serve_vue(catchall: str):
        return FileResponse(os.path.join(dist_path, "index.html"))
else:
    print(f"ВНИМАНИЕ: Папка {dist_path} не найдена. Раздача фронтенда отключена.")