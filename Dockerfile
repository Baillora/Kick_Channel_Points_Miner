FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libcurl4-openssl-dev \
        libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.11-slim

LABEL org.opencontainers.image.title="Kick Channel Points Miner" \
      org.opencontainers.image.description="Automated Kick channel-points farmer" \
      org.opencontainers.image.source="https://github.com/Baillora/Kick_Channel_Points_Miner"

RUN apt-get update && apt-get install -y --no-install-recommends \
        libcurl4 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local

WORKDIR /app

COPY . .

ENV PYTHONUNBUFFERED=1

EXPOSE 5000

CMD ["python", "main.py"]
