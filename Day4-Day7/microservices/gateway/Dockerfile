FROM python:3.10-slim

WORKDIR /app

COPY microservices/gateway/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY microservices/gateway/app /app/app
COPY frontend /app/frontend

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
