# Use an official Python runtime as a base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ACCEPT_EULA=Y

# Set working directory
WORKDIR /app

# Install system dependencies including Microsoft ODBC Driver and build tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends wget gnupg2 build-essential && \
    wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /usr/share/keyrings/microsoft-archive-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/microsoft-archive-keyring.gpg] https://packages.microsoft.com/ubuntu/22.04/prod jammy main" > /etc/apt/sources.list.d/microsoft.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends msodbcsql17 && \
    apt-get purge -y --auto-remove wget gnupg2 && \
    rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Copy only dependency files for caching
COPY pyproject.toml .
RUN uv pip install --system --no-cache gunicorn>=20.1.0 waitress>=2.1.0 flask>=2.0.0 requests>=2.25.0 python-dotenv>=0.19.0

# Copy application source code
COPY . .

# Create and switch to a non-root user
RUN useradd -m -r -s /bin/false appuser && chown -R appuser:appuser /app
USER appuser

# Expose the port your app runs on
EXPOSE 5000

# Use gunicorn to run the app in production
# CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]

# Use gunicorn to run the app in production with your config
CMD ["gunicorn", "--config", "gunicorn.py", "app:app"]