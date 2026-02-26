# --- Stage 1: grab Weaviate binary ---
FROM semitechnologies/weaviate:1.25.1 AS weaviate-src

# --- Stage 2: runtime ---
FROM python:3.11-slim

# HF Spaces expects port 7860
EXPOSE 7860

# Weaviate binary + its libs
COPY --from=weaviate-src /bin/weaviate /usr/local/bin/weaviate

# System deps
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Make startup script executable
RUN chmod +x start.sh

# Weaviate data dir
RUN mkdir -p /tmp/weaviate

CMD ["./start.sh"]
