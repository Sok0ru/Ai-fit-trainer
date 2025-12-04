FROM python:3.11-slim

# Установка системных зависимостей для SSL и сети
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir requests "urllib3<2"  # Фиксируем совместимую версию

# Копируем код
COPY . .

CMD ["python", "-m", "main"]
