FROM python:3.10-slim

# Instalar dependencias del sistema para Playwright/Chrome
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libpango-1.0-0 \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar requirements e instalar dependencias Python
COPY requirements.txt .
RUN pip install -r requirements.txt

# Instalar Playwright y Chromium
RUN playwright install chromium

# Copiar el código de la aplicación
COPY . .

# Ejecutar la aplicación
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}

