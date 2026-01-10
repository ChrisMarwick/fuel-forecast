FROM python:3.14-alpine

RUN pip install poetry

COPY . /api
WORKDIR /api
RUN poetry install
ENTRYPOINT ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]