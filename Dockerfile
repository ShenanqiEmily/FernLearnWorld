FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps: libjpeg/zlib for Pillow (profile picture thumbnails)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libjpeg62-turbo-dev \
        zlib1g-dev \
        libpq-dev \
        gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/production.txt

COPY . .
RUN chmod +x docker-entrypoint.sh

# Static files don't need a DB connection, safe to collect at build time.
# DEBUG/SECRET_KEY are read from env at runtime, but collectstatic only
# needs STATIC_ROOT/STATICFILES_DIRS, which don't depend on either.
RUN SECRET_KEY=build-time-placeholder python manage.py collectstatic --noinput

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
