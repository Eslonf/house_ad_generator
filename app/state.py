import asyncio

# Асинхронная очередь для задач
TASK_QUEUE = asyncio.Queue()
# Словарь для хранения результатов
TASK_RESULTS = {}