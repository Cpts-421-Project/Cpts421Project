FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Non-root user for security
RUN addgroup --system app && adduser --system --ingroup app app

COPY src/ src/
COPY alembic.ini .
COPY alembic/ alembic/

ENV PYTHONPATH=/app/src

RUN chown -R app:app /app
USER app

EXPOSE 8000

# Railway injects PORT dynamically; fall back to 8000 for local Docker usage
CMD ["sh", "-c", "alembic upgrade head && uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
