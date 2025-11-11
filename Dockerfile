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
    libasound2

# Instalar dependencias Python
RUN pip install fastapi uvicorn playwright

# Instalar Chromium
RUN playwright install chromium

# Crear directorio de trabajo
WORKDIR /app

# Copiar código
COPY . .

# Ejecutar la aplicación con puerto fijo
CMD ["python", "main.py"]
