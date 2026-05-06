# --- ЭТАП 1: Сборка Vue.js ---
FROM node:24-slim as build-stage
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# --- ЭТАП 2: Бэкенд на Python ---
FROM python:3.12-slim
WORKDIR /app

# Устанавливаем зависимости Python
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код бэкенда
COPY backend/ ./backend

# Копируем собранный фронтенд из первого этапа
COPY --from=build-stage /app/frontend/dist ./frontend/dist

WORKDIR /app/backend
EXPOSE 7860
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]