# Use lightweight Python image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Install additional utilities
RUN apt update && apt install -y curl net-tools procps

# Copy the application code
COPY . /app

# Expose port for logs ingestion
EXPOSE 8000

# Run the log processing script
CMD ["python", "preprocess_metrics.py"]
