FROM python:3.10-bullseye

# Instalar dependencias necesarias para Chromium y Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libasound2 \
    fonts-liberation \
    libappindicator3-1 \
    libu2f-udev \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar Playwright y Chromium de forma persistente
RUN python -m playwright install chromium

# Copiar el código fuente
COPY . .

# Exponer el puerto (Railway lo inyecta, pero sirve localmente)
EXPOSE 8000

# Ejecutar la aplicación con Uvicorn
CMD ["python", "main.py"]
