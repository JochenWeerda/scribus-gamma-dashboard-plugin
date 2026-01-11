FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy package
COPY . /app

# Set environment variables
ENV PYTHONPATH=/app:/packages
ENV CHROMA_DB_PATH=/app/chroma_db
ENV EMBEDDING_MODEL=paraphrase-multilingual-mpnet-base-v2
ENV CLIP_MODEL=clip-ViT-B-32

# Create chroma_db directory
RUN mkdir -p /app/chroma_db

# Expose port (falls RAG als separater Service läuft)
# EXPOSE 8005

CMD ["python", "-m", "packages.rag_service"]

