# Etapa base: Python pequeño con logs sin buffer y sin archivos .pyc.
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

# Instala dependencias primero para aprovechar la caché si cambia solo el código.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copia la API, modelos, configuración de base y seed.
COPY . .

# Desarrollo: Uvicorn reinicia el servidor cuando cambia el código montado.
FROM base AS development
EXPOSE 8001
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]

# Producción: servidor ASGI sin autoreload.
FROM base AS production
EXPOSE 8001
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
