FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml poetry.lock* /app/
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-root

COPY . /app

CMD ["python", "data_pipeline/main.py"]