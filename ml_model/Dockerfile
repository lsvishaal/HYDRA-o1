# Use a lightweight Python image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt --upgrade

# Copy the entire ML model directory
COPY . /app

# Expose the API port
EXPOSE 8500

# Run the ML model API
CMD ["python", "predict.py"]
