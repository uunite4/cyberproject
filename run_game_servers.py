#!/usr/bin/env python3
import subprocess

# ----------------------------
# Paths
# ----------------------------
DOCKER_DIR = "game"           # folder containing Dockerfile
DOCKERFILE = "game/game_server.Dockerfile"  # forward slashes for Docker
HOST_PROJECT_PATH = DOCKER_DIR
CONTAINER_PROJECT_PATH = "/app"

# ----------------------------
# Docker image
# ----------------------------
IMAGE = "game_server:latest"

# ----------------------------
# Servers
# ----------------------------
SERVERS = [
    (9000, 1),
    (9001, 2),
    (9002, 3),
    (9003, 4),
]

SERVER_HOST_PORT = 9000

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
# Step 2: Run containers
# ----------------------------
for host_port, server_number in SERVERS:
    container_name = f"game{server_number}"
    print(f"Starting container {container_name} on host port {host_port} with SERVER_NUMBER={server_number}")

    # Stop and remove old container
    subprocess.run(
        ["docker", "rm", "-f", container_name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # Run new container with UDP port mapping, environment variable, and mounted volume
    subprocess.run([
        "docker", "run", "-d",
        "-p", f"{host_port}:{SERVER_HOST_PORT}/udp",
        "--name", container_name,
        "-e", f"SERVER_NUMBER={server_number}",
        "-v", f"{HOST_PROJECT_PATH}:{CONTAINER_PROJECT_PATH}",
        IMAGE
    ])

print("\nAll containers started successfully!")