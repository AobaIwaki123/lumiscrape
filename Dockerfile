FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy project files & source code
COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY tools/ ./tools/

# Install Python dependencies using uv
RUN uv pip install --system .

ENV PYTHONPATH="/app/src"

# Default entrypoint for Scrapy crawler
WORKDIR /app/src/scrapers/scrapy_project
ENTRYPOINT ["scrapy"]
CMD ["list"]
