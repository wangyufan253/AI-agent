FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY tests ./tests
COPY samples ./samples
COPY scripts ./scripts

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .[dev]

ENTRYPOINT ["python", "-m", "harness_ai_learning"]
