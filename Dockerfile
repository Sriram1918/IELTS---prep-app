FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Railway uses PORT env variable
ENV PORT=8000
EXPOSE $PORT

# Use shell form to expand PORT variable
CMD uvicorn momentum_engine.main:app --host 0.0.0.0 --port $PORT
