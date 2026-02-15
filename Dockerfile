FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# Default: API service
CMD ["gunicorn","-k","uvicorn.workers.UvicornWorker","-w","2","-b","0.0.0.0:8080","app.api_service:app"]
