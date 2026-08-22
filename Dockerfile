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

# Copy dependency specifications
COPY pyproject.toml ./

# Install Python dependencies
RUN uv pip install --system -r pyproject.toml

# Copy source code
COPY src/ ./src/
COPY tools/ ./tools/

ENV PYTHONPATH="/app/src"

# Default entrypoint for Scrapy crawler
WORKDIR /app/src/scrapers/scrapy_project
ENTRYPOINT ["scrapy"]
CMD ["list"]
