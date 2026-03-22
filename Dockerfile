# Use lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir \
    cryptography \
    qh3

# Expose load balancer port
EXPOSE 8050

# Run load balancer
CMD ["python", "load_balancer.py"]