# Dockerfile for dlq-consumer application
# This image sets up a lightweight Python environment to run the Dead Letter Queue (DLQ) consumer service.

# Use a minimal Python 3.9 image to reduce image size and improve startup time
FROM python:3.9-slim

# Set the working directory within the container
WORKDIR /app

# Copy and install dependencies from requirements file without caching to keep image size small
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container's working directory
COPY . .

# Set the default command to run the DLQ consumer script
CMD ["python", "dlq_consumer.py"]
