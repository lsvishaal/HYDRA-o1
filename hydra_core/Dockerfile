# Use lightweight Python image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install necessary dependencies
RUN apt update && apt install -y curl net-tools procps && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt --upgrade

# Copy application files
COPY . /app

# Expose Flask default port
EXPOSE 5000

# Ensure that the app runs ONLY IF a valid Flask entrypoint is found
CMD ["bash", "-c", "if [ -f app.py ] || [ -f main.py ]; then gunicorn -w 4 -b 0.0.0.0:5000 app:app || gunicorn -w 4 -b 0.0.0.0:5000 main:app; else echo '❌ No Flask entrypoint (app.py or main.py) found in /app. Please place your Flask app correctly.'; exit 1; fi"]
