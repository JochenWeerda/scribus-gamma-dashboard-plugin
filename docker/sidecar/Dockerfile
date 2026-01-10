FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY packages/common/requirements.txt /tmp/common-requirements.txt
COPY packages/artifact_store/requirements.txt /tmp/store-requirements.txt
COPY apps/sidecar-mcp/requirements.txt /tmp/sidecar-requirements.txt

RUN pip install --no-cache-dir -r /tmp/common-requirements.txt && \
    pip install --no-cache-dir -r /tmp/store-requirements.txt && \
    pip install --no-cache-dir -r /tmp/sidecar-requirements.txt

# Copy packages
COPY packages /packages

# Copy app
COPY apps/sidecar-mcp /app

# Make packages importable
ENV PYTHONPATH=/app:/

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]

