FROM python:3.10

RUN apt update && apt install netcat-traditional -y  && rm -rf /var/lib/apt/lists/*

WORKDIR /code

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app
COPY ./publication_sources_policies.yaml /code/publication_sources_policies.yaml

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]