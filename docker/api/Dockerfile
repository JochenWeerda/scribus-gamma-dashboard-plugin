FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY packages/common/requirements.txt /tmp/common-requirements.txt
COPY packages/layout_schema/requirements.txt /tmp/schema-requirements.txt
COPY packages/artifact_store/requirements.txt /tmp/store-requirements.txt
COPY packages/event_bus/requirements.txt /tmp/event-bus-requirements.txt
COPY packages/cache/requirements.txt /tmp/cache-requirements.txt
COPY apps/api-gateway/requirements.txt /tmp/api-requirements.txt

RUN pip install --no-cache-dir -r /tmp/common-requirements.txt && \
    pip install --no-cache-dir -r /tmp/schema-requirements.txt && \
    pip install --no-cache-dir -r /tmp/store-requirements.txt && \
    pip install --no-cache-dir -r /tmp/event-bus-requirements.txt && \
    pip install --no-cache-dir -r /tmp/cache-requirements.txt && \
    pip install --no-cache-dir -r /tmp/api-requirements.txt

# Copy packages
COPY packages /packages

# Copy app
COPY apps/api-gateway /app

# Make packages importable
ENV PYTHONPATH=/app:/

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

