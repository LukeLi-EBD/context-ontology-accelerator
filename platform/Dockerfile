FROM python:3.12-slim AS builder

ARG PIP_INDEX_URL=https://pypi.org/simple
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /build
COPY requirements.txt ./
RUN pip install --index-url "${PIP_INDEX_URL}" -r requirements.txt

FROM python:3.12-slim

# S14H OCR/格式转换工具链（唯一一次重建；tesseract 纯 CPU + LibreOffice headless）
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tesseract-ocr tesseract-ocr-eng tesseract-ocr-chi-sim \
        libreoffice-impress libreoffice-writer \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app/src"

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY src ./src
COPY tests ./tests
COPY web ./web
COPY examples ./examples
RUN mkdir -p /data \
    && printf '#!/bin/sh\nexec python -m platform_core.cli "$@"\n' > /usr/local/bin/platform \
    && chmod +x /usr/local/bin/platform

EXPOSE 8080
ENTRYPOINT ["platform"]
CMD ["serve", "--config", "/data/platform.yaml"]
