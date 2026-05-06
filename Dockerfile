FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

RUN pip install poetry

COPY poetry.lock pyproject.toml ./

RUN poetry install --no-interaction --no-ansi --no-root --only=main

COPY . .

CMD ["poetry", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]