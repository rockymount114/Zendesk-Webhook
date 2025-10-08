# Use an official Python runtime as a base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install required packages for Microsoft ODBC setup
RUN apt-get update && apt-get install -y wget gnupg2

# Add Microsoft ODBC repository
RUN wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /usr/share/keyrings/microsoft-archive-keyring.gpg \
 && echo "deb [signed-by=/usr/share/keyrings/microsoft-archive-keyring.gpg] https://packages.microsoft.com/ubuntu/22.04/prod jammy main" > /etc/apt/sources.list.d/microsoft.list

# Accept the EULA before installing ODBC Driver 17
ENV ACCEPT_EULA=Y
RUN apt-get update && apt-get install -y msodbcsql17

# Install uv (use pipx, or pip)
RUN pip install uv

# Copy uv requirements (for example, pyproject.toml and optionally requirements.txt or requirements.lock)
COPY pyproject.toml pyproject.toml

# Install dependencies using uv — adjust flags if needed
RUN uv pip install --system --upgrade -r requirements.lock

# Copy app files
COPY . .

# Copy .env file
COPY .env .

# Expose the port your app runs on
EXPOSE 5000

# Command to run your app
CMD ["python", "app.py"]
