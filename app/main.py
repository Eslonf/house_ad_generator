import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers import generator_page
from app.ml_model.processing import generate_ad_from_image

from app.state import TASK_QUEUE, TASK_RESULTS

async def worker():
    """
    Фоновый "работник", который в бесконечном цикле берет задачи из очереди,
    выполняет их и сохраняет результат.
    """
    print("Воркер запущен и готов к работе...")
    while True:
        # Ждем, пока в очереди появится новая задача
        task = await TASK_QUEUE.get()
        task_id = task["task_id"]
        image_bytes = task["image_bytes"]
        style = task["style"]

        print(f"Воркер взял в работу задачу: {task_id}")
        try:
            result = await asyncio.to_thread(generate_ad_from_image, image_bytes, style)
            TASK_RESULTS[task_id] = {"status": "completed", "data": result}
            print(f"Задача {task_id} успешно выполнена.")
        except Exception as e:
            print(f"Ошибка при выполнении задачи {task_id}: {e}")
            TASK_RESULTS[task_id] = {"status": "failed", "error": str(e)}
        finally:
            # Сообщаем очереди, что задача обработана
            TASK_QUEUE.task_done()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управляет жизненным циклом приложения. Запускает фонового воркера при старте.
    """
    # Запускаем нашего воркера как фоновую задачу
    asyncio.create_task(worker())
    yield

app = FastAPI(title="Генератор объявлений", lifespan=lifespan)

# Подключаем роутер и статику
app.include_router(generator_page.router)
app.mount("/static", StaticFiles(directory="app/static"), name="static")