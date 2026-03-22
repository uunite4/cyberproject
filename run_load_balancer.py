#!/usr/bin/env python3
import subprocess

# ----------------------------
# Load .env
# ----------------------------
LOAD_BALANCER_PORT = 9050
LOAD_BALANCER_HOST_PORT = 9050
GAME_SERVER_1 = "192.168.68.110:9000"
GAME_SERVER_2 = "192.168.68.110:9001"
GAME_SERVER_3 = "192.168.68.110:9002"
GAME_SERVER_4 = "192.168.68.110:9003"

# ----------------------------
# Paths
# ----------------------------
DOCKER_DIR = "loadbalancer"  # folder containing Dockerfile
DOCKERFILE = "loadbalancer/load_balancer.Dockerfile"
HOST_PROJECT_PATH = DOCKER_DIR
CONTAINER_PROJECT_PATH = "/app"

# ----------------------------
# Docker image
# ----------------------------
IMAGE = "load_balancer:latest"

# ----------------------------
# Step 1: Build image
# ----------------------------

container_name = "load_balancer"

subprocess.run(["docker", "rm", "-f", container_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Build fresh image
subprocess.run([
    "docker", "build",
    "--no-cache",
    "-t", IMAGE,
    "-f", DOCKERFILE,
    DOCKER_DIR
], check=True)

# Run new container with port mapping, environment variable, and mounted volume
subprocess.run([
    "docker", "run", "-d",
    "-p", f"{LOAD_BALANCER_PORT}:{LOAD_BALANCER_HOST_PORT}/udp",
    "--name", container_name,
    "-e", f"LOAD_BALANCER_PORT={LOAD_BALANCER_PORT}",
    "-e", f"GAME_SERVER_1={GAME_SERVER_1}",
    "-e", f"GAME_SERVER_2={GAME_SERVER_2}",
    "-e", f"GAME_SERVER_3={GAME_SERVER_3}",
    "-e", f"GAME_SERVER_4={GAME_SERVER_4}",
    IMAGE
])

print("\nLoad balancer container started successfully!")
