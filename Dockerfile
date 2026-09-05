# ConnectHub — Real-world Dockerfile (Railway/Render/Fly)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps (Pillow ke liye)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg-dev zlib1g-dev libpq-dev gcc \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Static collect (WhiteNoise ke liye, build time pe)
RUN python manage.py collectstatic --noinput || true

# Gunicorn (prod server) — Railway Render auto PORT env deta hai
CMD gunicorn connect_hub.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 60 --log-file -
