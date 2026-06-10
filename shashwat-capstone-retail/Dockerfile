FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app
ENV API_HOST=0.0.0.0
ENV API_PORT=8080
ENV RESOURCES_DIR=/app/data/Resources
ENV OUTPUT_DIR=/app/outputs
ENV PROMPTS_DIR=/app/prompts
ENV VECTOR_DB_PROVIDER=pinecone
ENV EMBEDDING_DIMENSION=768

RUN mkdir -p /app/outputs /app/data

EXPOSE 8080

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
