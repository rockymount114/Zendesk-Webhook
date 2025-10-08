# Use an official Python runtime as a base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ACCEPT_EULA=Y

# Set working directory
WORKDIR /app

# Install system dependencies including Microsoft ODBC Driver
# and clean up to reduce image size.
RUN apt-get update && \
    apt-get install -y --no-install-recommends wget gnupg2 && \
    wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /usr/share/keyrings/microsoft-archive-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/microsoft-archive-keyring.gpg] https://packages.microsoft.com/ubuntu/22.04/prod jammy main" > /etc/apt/sources.list.d/microsoft.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends msodbcsql17 && \
    apt-get purge -y --auto-remove wget gnupg2 && \
    rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy application files (respecting .dockerignore)
COPY . .

# Install python dependencies for production
# The build backend (hatchling) needs the source files to be present.
RUN uv pip install --system ".[production]"

# Create and switch to a non-root user
RUN useradd -m -r -s /bin/false appuser && chown -R appuser:appuser /app
USER appuser

# Expose the port your app runs on
EXPOSE 5000

# Use gunicorn to run the app in production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
