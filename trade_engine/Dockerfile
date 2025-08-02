# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Build arguments
ARG VECTORBT_TOKEN

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# TA-Lib installation removed for simplified build

# Copy requirements
COPY trade_engine/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 trader

# TA-Lib copying removed for simplified build

# Copy installed packages from builder
COPY --from=builder /root/.local /home/trader/.local

# Fix ownership
RUN chown -R trader:trader /home/trader/.local

# Copy trade_common
COPY --chown=trader:trader trade_common /app/trade_common

# Install trade_common as user
USER trader
RUN cd /app/trade_common && pip install --user -e .
USER root

# Copy application code
COPY --chown=trader:trader trade_engine/. .

# Create necessary directories
RUN mkdir -p /app/logs /app/data && chown -R trader:trader /app/logs /app/data

# Switch to non-root user
USER trader

# Update PATH
ENV PATH=/home/trader/.local/bin:$PATH

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Run the application
CMD ["python", "main.py"]