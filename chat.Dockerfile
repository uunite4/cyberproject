# Use lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir \
    pygame \
    cryptography \
    qh3 \
    protobuf

# Expose chat port (from your SETTINGS)
EXPOSE 8000

# Run chat server
CMD ["python", "chat_server.py"]