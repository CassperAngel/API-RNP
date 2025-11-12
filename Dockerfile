FROM python:3.10-slim

# Instalar dependencias del sistema
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
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar requirements actualizado
COPY requirements.txt .
RUN pip install -r requirements.txt

# Forzar instalación limpia de Chromium
RUN playwright install chromium --force

COPY . .

CMD ["python", "main.py"]
