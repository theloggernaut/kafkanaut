# Dockerfile for my-python-consumer application
# This image sets up a lightweight Python environment to run the consumer service.

# Use a lightweight Python 3.9 image
FROM python:3.9-slim

# Set the working directory within the container
WORKDIR /app

# Copy requirements file and install dependencies without caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container's working directory
COPY . .

# Set the default command to run the consumer script
CMD ["python", "consumer.py"]

