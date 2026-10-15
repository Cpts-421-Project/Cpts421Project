FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Non-root user for security
RUN addgroup --system app && adduser --system --ingroup app app

COPY src/ src/
COPY data/ data/
COPY seed_db.py .
COPY alembic.ini .
COPY alembic/ alembic/

ENV PYTHONPATH=/app/src

RUN chown -R app:app /app
USER app

EXPOSE 8000

# Bind to :: (IPv6 wildcard + dual-stack IPv4) for Railway Private Networking
CMD ["sh", "-c", "alembic upgrade head && python seed_db.py && uvicorn src.main:app --host '::' --port ${PORT:-8000}"]
