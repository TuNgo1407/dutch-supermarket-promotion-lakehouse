FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY .env .
COPY src/ ./src/

CMD ["python","src/runWeeklyPipeline.py"]



