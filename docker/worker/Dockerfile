FROM ubuntu:22.04

# Set timezone to avoid interactive prompt
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Berlin

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tzdata \
    python3.11 \
    python3-pip \
    xvfb \
    x11vnc \
    fluxbox \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Scribus (headless)
# Note: Scribus muss für headless Betrieb kompiliert werden oder aus Paketquellen installiert
# Für MVP: Wir verwenden einen Dummy-Export (siehe worker code)
# RUN apt-get install -y scribus || echo "Scribus muss manuell installiert werden"

WORKDIR /app

# Install Python dependencies
COPY packages/common/requirements.txt /tmp/common-requirements.txt
COPY packages/artifact_store/requirements.txt /tmp/store-requirements.txt
COPY packages/layout_schema/requirements.txt /tmp/schema-requirements.txt
COPY packages/sla_compiler/requirements.txt /tmp/compiler-requirements.txt
COPY apps/worker-scribus/requirements.txt /tmp/worker-requirements.txt

RUN pip3 install --no-cache-dir -r /tmp/common-requirements.txt && \
    pip3 install --no-cache-dir -r /tmp/store-requirements.txt && \
    pip3 install --no-cache-dir -r /tmp/schema-requirements.txt && \
    pip3 install --no-cache-dir -r /tmp/compiler-requirements.txt && \
    pip3 install --no-cache-dir -r /tmp/worker-requirements.txt

# Copy packages
COPY packages /packages

# Copy app
COPY apps/worker-scribus /app

# Make packages importable
ENV PYTHONPATH=/app:/
ENV DISPLAY=:99

# Start Xvfb in background (wird im Entrypoint-Script gestartet)
CMD ["python3", "worker.py"]

