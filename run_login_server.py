#!/usr/bin/env python3
import subprocess

# ----------------------------
# Load .env
# ----------------------------
LOGIN_SERVER_PORT = 8050
LOGIN_HOST_PORT = 8050

LOAD_BALANCER = "192.168.68.110:9050"

GAME_SERVER_1 = "192.168.68.110:9000"
GAME_SERVER_2 = "192.168.68.110:9001"
GAME_SERVER_3 = "192.168.68.110:9002"
GAME_SERVER_4 = "192.168.68.110:9003"

# ----------------------------
# Paths
# ----------------------------
DOCKER_DIR = "loginserver"  # folder containing Dockerfile
DOCKERFILE = "loginserver/login_server.Dockerfile"
HOST_PROJECT_PATH = DOCKER_DIR
CONTAINER_PROJECT_PATH = "/app"

# ----------------------------
# Docker image
# ----------------------------
IMAGE = "login_server:latest"

container_name = "login_server"
# Stop old container
subprocess.run(["docker", "rm", "-f", container_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Build fresh image
subprocess.run([
    "docker", "build",
    "--no-cache",
    "-t", IMAGE,
    "-f", DOCKERFILE,
    DOCKER_DIR
], check=True)

# Run container without volume if you want the new code
subprocess.run([
    "docker", "run", "-d",
    "-p", f"{LOGIN_SERVER_PORT}:{LOGIN_HOST_PORT}/udp",
    "--name", container_name,
    "-e", f"LOGIN_SERVER_PORT={LOGIN_SERVER_PORT}",
    "-e", f"LOAD_BALANCER={LOAD_BALANCER}",
    "-e", f"GAME_SERVER_1={GAME_SERVER_1}",
    "-e", f"GAME_SERVER_2={GAME_SERVER_2}",
    "-e", f"GAME_SERVER_3={GAME_SERVER_3}",
    "-e", f"GAME_SERVER_4={GAME_SERVER_4}",
    IMAGE
])

print("\nLogin server container started successfully!")
