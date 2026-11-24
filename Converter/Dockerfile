FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN groupadd --gid 10001 appuser && \
    useradd --uid 10001 --gid appuser --shell /bin/sh --create-home appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN sed -i 's/\r$//' /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh && \
    export DJANGO_SECRET_KEY="$(python -c 'from secrets import token_urlsafe; print(token_urlsafe(50))')" && \
    DB_ENGINE=django.db.backends.sqlite3 DB_NAME=:memory: \
        python manage.py makemigrations Converter_app --noinput && \
    python manage.py collectstatic --noinput && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8002

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "Converter.wsgi:application", "--bind", "0.0.0.0:8002", "--worker-class", "gthread", "--workers", "1", "--threads", "4", "--timeout", "60", "--access-logfile", "-"]
