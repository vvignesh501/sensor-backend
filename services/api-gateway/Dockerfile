FROM python:3.9-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn httpx

COPY services/api-gateway/main.py .

EXPOSE 8000

CMD ["python", "main.py"]
