FROM python:3.10-slim

WORKDIR /app

# Instalacja zależności systemowych dla GDAL/Rasterio
RUN apt-get update && apt-get install -y \
    libexpat1 \
    && rm -rf /var/lib/apt/lists/*
# Dodajemy libpq-dev dla obsługi PostGIS/Postgres
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-keep-alive", "300"]