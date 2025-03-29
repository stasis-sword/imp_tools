FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# local dev only
COPY service_account.json .
COPY . .

ENV PYTHONUNBUFFERED=1
ENV PORT=8080

CMD ["python", "entrypoint.py"]
