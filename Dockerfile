# 1. Use a lightweight official Python Linux image
FROM python:3.12-slim

# 2. Prevent Python from writing .pyc files & force unbuffered logs (critical for container logging)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Set working directory inside the container
WORKDIR /app

# 4. Copy ONLY requirements first to leverage Docker layer caching
# (If code changes but requirements.txt doesn't, Docker skips re-downloading packages!)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the application code
COPY ./app ./app

# 6. Create a non-root user for security (never run production containers as root)
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser:appuser /app
USER appuser

# 7. Expose the application port
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-perios=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1
# 8. Start the production ASGI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]