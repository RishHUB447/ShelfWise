FROM python:3.13-slim

WORKDIR /app

# Install system dependencies, including libgomp1
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    libgomp1 \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

CMD sh -c "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"