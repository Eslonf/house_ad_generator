import torch
from PIL import Image
from transformers import pipeline
from huggingface_hub import hf_hub_download
from llama_cpp import Llama
import io

# --- ГЛОБАЛЬНАЯ ЗАГРУЗКА МОДЕЛЕЙ (ВЫПОЛНЯЕТСЯ ОДИН РАЗ ПРИ СТАРТЕ ПРИЛОЖЕНИЯ) ---

print("Загрузка ML-моделей... Это может занять время.")
MODELS_LOADED = False

try:
    # Загрузка Модели 1 (VQA)
    # VQA-модель довольно легкая, ее можно оставить на CPU
    vqa_pipeline = pipeline(
        "visual-question-answering",
        model="Salesforce/blip-vqa-base",
        device="cpu"
    )

    # Загрузка Модели 2 (Gemma GGUF)
    model_name_gguf = "unsloth/gemma-3-4b-it-GGUF"
    model_file = "gemma-3-4b-it-Q3_K_M.gguf"
    model_path = hf_hub_download(repo_id=model_name_gguf, filename=model_file)
    
    # Инициализируем для работы на CPU
    gemma_gguf_model = Llama(
        model_path=model_path,
        n_ctx=2048,
        n_gpu_layers=0,
        verbose=False
    )

    MODELS_LOADED = True
    print("Все ML-модели успешно загружены!")

except Exception as e:
    print(f"КРИТИЧЕСКАЯ ОШИБКА при загрузке моделей: {e}")

# Список вопросов, которые мы будем задавать VQA-модели
QUESTIONS_TO_ASK = {
    "Материал стен": "What is the primary material of the exterior walls?",
    "Количество этажей": "How many floors does the house have?",
    "Цвет крыши": "What color is the roof?",
    "Архитектурный стиль": "What is the architectural style of the house?",
    "Гараж": "Is there a garage?",
    "Озеленение": "What does the landscaping look like?",
}

PROMPT_INSTRUCTIONS = {
    "brief": "Ты — копирайтер, который пишет короткие, яркие и продающие объявления для недвижимости (4-5 предложений).",
    "professional": "Ты — риелтор, который составляет детальное и структурированное объявление для листинга на сайте недвижимости. Опиши преимущества, используя профессиональный и деловой стиль.",
    "social": "Ты — SMM-менеджер, который пишет яркий и вовлекающий пост для социальных сетей. Используй эмодзи, добавь несколько релевантных хэштегов и обращайся к аудитории неформально."
}

# --- ГЛАВНАЯ ФУНКЦИЯ ПАЙПЛАЙНА ---

def generate_ad_from_image(image_bytes: bytes, style: str) -> dict:
    """
    Принимает изображение и стиль, анализирует и генерирует объявление.
    """
    if not MODELS_LOADED:
        raise RuntimeError("Модели не были загружены.")

    try:
        image = Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        raise ValueError(f"Не удалось прочитать изображение: {e}")

    # 1. Сбор характеристик с помощью VQA
    print("Анализ изображения...")
    house_characteristics = {}
    for key, question in QUESTIONS_TO_ASK.items():
        answer = vqa_pipeline(image, question=question, top_k=1)
        characteristic = answer[0]['answer']
        house_characteristics[key] = characteristic

    # 2. Создание промпта для Gemma
    print(f"Создание промпта в стиле '{style}'...")
    prompt_details = ""
    for key, value in house_characteristics.items():
        prompt_details += f"- {key}: {value}\n"

    # Выбираем нужную инструкцию из словаря. Если стиль неизвестен, используем "brief".
    instruction = PROMPT_INSTRUCTIONS.get(style, PROMPT_INSTRUCTIONS["brief"])

    prompt = f"""<start_header_id>user<end_header_id>
{instruction}

Вот характеристики дома:
{prompt_details}
Напиши объявление.<end_header_id>
<start_header_id>model<end_header_id>
"""

    # 3. Генерация текста объявления
    print("Генерация объявления...")
    response = gemma_gguf_model(
        prompt,
        max_tokens=200,
        temperature=1.0,
        top_k=64,
        top_p=0.95,
        min_p=0.0,
        stop=["<end_header_id>"],
    )
    ad_text = response['choices'][0]['text'].strip()
    
    # 4. Постобработка текста
    if ad_text and not ad_text.endswith(('.', '!', '?')):
        last_sentence_end = max(ad_text.rfind('.'), ad_text.rfind('!'), ad_text.rfind('?'))
        if last_sentence_end != -1:
            ad_text = ad_text[:last_sentence_end + 1]

    print("Генерация завершена.")
    return {
        "characteristics": house_characteristics,
        "ad_text": ad_text
    }