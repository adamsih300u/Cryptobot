# Stage 1: Build stage
FROM python:3.11-slim as builder

# Create non-root user
RUN groupadd -r botuser && useradd -r -g botuser botuser

# Set working directory and ownership
WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY --chown=botuser:botuser requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv /build/venv
ENV PATH="/build/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime stage
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r botuser && useradd -r -g botuser botuser

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder --chown=botuser:botuser /build/venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Copy application files
COPY --chown=botuser:botuser bot.py .
COPY --chown=botuser:botuser cryptotracker.py .
COPY --chown=botuser:botuser reminder.py .
COPY --chown=botuser:botuser fortunes.py .
COPY --chown=botuser:botuser bot_data.json .

# Create and set permissions for data directory
RUN mkdir -p /app/data && chown -R botuser:botuser /app/data

# Create volume for persistent data
VOLUME ["/app/data"]

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/venv/bin:$PATH"

# Switch to non-root user
USER botuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('https://api.telegram.org')" || exit 1

# Run the bot
CMD ["python", "bot.py"] 
