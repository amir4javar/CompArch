# ── Stage 1: pull Weaviate binary from the official image ─────────────────────
FROM semitechnologies/weaviate:1.25.1 AS weaviate-source

# ── Stage 2: application ──────────────────────────────────────────────────────
FROM python:3.11-slim

# Copy the Weaviate binary from the official image
COPY --from=weaviate-source /bin/weaviate /usr/local/bin/weaviate
RUN chmod +x /usr/local/bin/weaviate

# musl: Weaviate binary is Alpine-built (musl libc); curl: health-check in start.sh
RUN apt-get update && apt-get install -y --no-install-recommends curl musl && \
    ln -s /usr/lib/x86_64-linux-musl/libc.so /lib/ld-musl-x86_64.so.1 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project (PDFs included — needed for indexing)
COPY . .

# Directory where Weaviate stores its data (ephemeral in HF Spaces free tier)
RUN mkdir -p /app/weaviate_data

RUN chmod +x start.sh

# HF Spaces requires port 7860
EXPOSE 7860

CMD ["./start.sh"]
