FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ../shared /app/shared
COPY . .

EXPOSE 8003
CMD ["uvicorn", "service:app", "--host", "0.0.0.0", "--port", "8003"]
