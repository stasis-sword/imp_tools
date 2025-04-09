FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN if [ ! -f service_account.json ]; then \
    echo '{"type":"service_account","note":"This is a placeholder file. In production, use GOOGLE_APPLICATION_CREDENTIALS environment variable."}' > service_account.json; \
    fi

ENV PYTHONUNBUFFERED=1
ENV PORT=8080

CMD ["python", "entrypoint.py"]
