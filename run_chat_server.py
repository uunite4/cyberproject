#!/usr/bin/env python3
import subprocess

# ----------------------------
# Load .env
# ----------------------------
CHAT_SERVER_PORT = 8000
CHAT_HOST_PORT = 8000

# ----------------------------
# Paths
# ----------------------------
DOCKER_DIR = "chat"  # folder containing Dockerfile
DOCKERFILE = "chat/chat_server.Dockerfile"
HOST_PROJECT_PATH = DOCKER_DIR
CONTAINER_PROJECT_PATH = "/app"

# ----------------------------
# Docker image
# ----------------------------
IMAGE = "chat_server:latest"

# ----------------------------
# Step 1: Build image
# ----------------------------
print("Building Docker image...")
subprocess.run([
    "docker", "build",
    "-t", IMAGE,
    "-f", DOCKERFILE,
    DOCKER_DIR
], check=True)
print("Docker image built successfully!\n")

# ----------------------------
# Step 2: Run container
# ----------------------------
container_name = "chat_server"
print(f"Starting container {container_name} on host port {CHAT_SERVER_PORT}")

# Stop and remove old container
subprocess.run(
    ["docker", "rm", "-f", container_name],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)

# Run new container with port mapping, environment variable, and mounted volume
subprocess.run([
    "docker", "run", "-d",
    "-p", f"{CHAT_SERVER_PORT}:{CHAT_HOST_PORT}/udp",
    "--name", container_name,
    "-e", f"CHAT_SERVER_PORT={CHAT_SERVER_PORT}",
    "-v", f"{HOST_PROJECT_PATH}:{CONTAINER_PROJECT_PATH}",
    IMAGE
])

print("\nChat server container started successfully!")
