FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt httpx

COPY services/sensor-service/main.py .

EXPOSE 8002

CMD ["python", "main.py"]
