FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    stockfish \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/src/ ./src/
COPY scripts/ ./scripts/

RUN chmod +x ./scripts/download_data.sh

EXPOSE 8097

CMD ["sh", "-c", "./scripts/download_data.sh && uvicorn src.main:app --host 0.0.0.0 --port 8097 --reload"]
