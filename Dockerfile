FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY pyproject.toml README.md alembic.ini constraints-docker-cpu.txt ./
COPY api/ api/
COPY alembic/ alembic/
COPY config/ config/
COPY src/ src/
RUN python -m pip install --no-cache-dir \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    --constraint constraints-docker-cpu.txt \
    '.[local-models]'
RUN mkdir -p /app/data/indexes && chown -R 10001:10001 /app

USER 10001:10001
EXPOSE 8100
CMD ["python", "-m", "uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8100"]
