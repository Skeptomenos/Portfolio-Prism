FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .
RUN pip install -e .

# Environment (non-sensitive)
ENV DOCKER_MODE=true
ENV PYTHONUNBUFFERED=1

# Sensitive env vars should be passed at runtime via:
# - docker run -e FINNHUB_API_KEY=xxx
# - docker-compose.yml environment section
# - .env file

# Expose Streamlit
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run
CMD ["streamlit", "run", "src/dashboard/app.py", \
     "--server.address=0.0.0.0", \
     "--server.port=8501", \
     "--browser.gatherUsageStats=false"]
