FROM python:3.13-slim-bookworm

# Install system dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install uv
ADD https://astral.sh/uv/install.sh /install.sh
RUN chmod 755 /install.sh && /install.sh && rm /install.sh

# Make uv available
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app

COPY . .

# Install dependencies using uv
RUN uv sync

# Activate virtual environment
ENV PATH="/app/.venv/bin:${PATH}"


EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
