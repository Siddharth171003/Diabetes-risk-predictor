# Use official Python image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory
WORKDIR /app

# Copy requirements and install (with timeout and reliable mirror)
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=100 -r requirements.txt -i https://pypi.org/simple

# Copy the entire app
COPY . .

# Expose Flask port
EXPOSE 5000

# Run the Flask app
CMD ["python", "app.py"]
