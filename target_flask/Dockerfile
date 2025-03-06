# Use lightweight Python image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install curl and dependencies
RUN apt update && apt install -y curl net-tools procps

# Copy `requirements.txt` only if it exists
COPY requirements.txt /app/
RUN test -f /app/requirements.txt && pip install --no-cache-dir -r /app/requirements.txt || echo "[⚠] No dependencies to install"

# Copy application files
COPY . /app/

# Expose Flask port
EXPOSE 5050

# Run Flask App with Gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5050", "app:app"]
