FROM python:3.10-slim-bullseye


# Instalar dependencias del sistema necesarias para Chromium/Playwright
RUN apt-get update && apt-get install -y \
    wget gnupg ca-certificates \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 \
    libxss1 libasound2 libpangocairo-1.0-0 libpango-1.0-0 libcairo2 \
    libx11-xcb1 libxcb1 libxi6 libfontconfig1 libxrender1 libxext6 \
    libxfixes3 libxtst6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar Chromium con todas sus dependencias
RUN playwright install chromium --with-deps

# Copiar código de la aplicación
COPY . .

# Ejecutar aplicación FastAPI
CMD ["python", "main.py"]
