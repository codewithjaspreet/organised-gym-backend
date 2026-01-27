FROM python:3.11-slim-bookworm

# Install system dependencies (REQUIRED for psycopg)
RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential \
    libpq-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install uv
ADD https://astral.sh/uv/install.sh /install.sh
RUN chmod 755 /install.sh && /install.sh && rm /install.sh

# Make uv available
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app

# Copy project
COPY . .

# Install dependencies
RUN uv sync

# Activate virtual environment
ENV PATH="/app/.venv/bin:${PATH}"

# App Runner port (MATCH THIS IN UI)
EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
