# Use an official lightweight Python 3.12 runtime
FROM python:3.12-slim

# Set environment variables to optimize Python container execution
# PYTHONDONTWRITEBYTECODE prevents Python from writing .pyc files to disc
# PYTHONUNBUFFERED forces stdout/stderr to stream directly to container logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies required for Pillow, OpenCV, and C-compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    libwebp-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Copy dependency requirements first to leverage Docker layer caching
# If requirements.txt doesn't change, Docker skips re-running pip install
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container
COPY . .

# Expose port 5000 for the Flask web traffic
EXPOSE 5000

# Default command for the Web Service (Render will override this for the Celery Worker)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
