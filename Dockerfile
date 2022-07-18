FROM python:3.10-slim

WORKDIR /code

COPY ./requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /tmp/requirements.txt

CMD ["uvicorn", "catalog.main:app", "--host", "0.0.0.0", "--port", "80", "--reload"]
