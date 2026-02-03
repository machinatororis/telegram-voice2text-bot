# Лёгкий образ с Python 3.12
FROM python:3.12-slim

# Не пишем .pyc и буферизуем stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Рабочая директория
WORKDIR /app

# Системные зависимости: ffmpeg + git (для надёжности) + build tools
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        build-essential \
        git \
    && rm -rf /var/lib/apt/lists/*

# Сначала ставим зависимости для облака
COPY requirements-cloud.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements-cloud.txt

# Копируем остальной код
COPY . .

# Открываем порт FastAPI
EXPOSE 8000

# По умолчанию запускаем FastAPI + webhook
CMD ["uvicorn", "webapp:app", "--host", "0.0.0.0", "--port", "8000"]
