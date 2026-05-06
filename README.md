---
title: AI House Ad Generator
emoji: 🏠
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# 🤖 Автоматический генератор объявлений о недвижимости

[![Test and Deploy](https://github.com/Eslonf/house_ad_generator/actions/workflows/ci.yml/badge.svg)](https://github.com/Eslonf/house_ad_generator/actions/workflows/ci.yml)

## 🚀 [Попробовать](https://huggingface.co/spaces/Eslonf/house_ad_generator)

Веб-приложение, которое использует две нейросетевые модели для автоматического создания рекламных объявлений на основе фотографий домов.

---

## ⚙️ Как это работает?

Приложение построено на асинхронной архитектуре с очередью задач, чтобы интерфейс оставался отзывчивым даже во время выполнения тяжелых ML-операций.

1.  **Загрузка фото:** Пользователь загружает изображение дома и выбирает желаемый стиль объявления.
2.  **Анализ изображения (Модель 1):** Модель **Visual Question Answering** "отвечает" на заранее заданные вопросы по изображению, извлекая его ключевые характеристики (материал стен, этажность и т.д.).
3.  **Генерация текста (Модель 2):** Легковесная языковая модель **Gemma** получает эти характеристики в виде промпта и пишет на их основе красивое рекламное объявление в заданном стиле.
4.  **Получение результата:** Клиент периодически опрашивает сервер, и как только задача выполнена, результат отображается на странице.

---

## 🛠️ Стек технологий

| Категория | Технология |
| :--- | :--- |
| **Язык** | **Python 3.12** |
| **Бэкенд (API)** | `FastAPI`, `Uvicorn` |
| **Фронтенд (SPA)**| `Vue.js 3`, `Vite`, `Axios`, `Bootstrap 5` |
| **ML Модели** | 1. VQA: [`Salesforce/blip-vqa-base`](https://huggingface.co/Salesforce/blip-vqa-base) <br> 2. LLM: [`unsloth/gemma-3-4b-it-GGUF`](https://huggingface.co/unsloth/gemma-3-4b-it-GGUF) |
| **Библиотеки** | `Transformers`, `llama-cpp-python`, `PyTorch` |
| **DevOps** | `GitHub Actions`, `Pytest`, `Docker` (Multi-stage build) |
