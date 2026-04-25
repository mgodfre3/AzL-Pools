FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo-dev libpng-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ../shared /app/shared
COPY . .

EXPOSE 8001
CMD ["uvicorn", "service:app", "--host", "0.0.0.0", "--port", "8001"]
