import subprocess
from pathlib import Path

import yaml

BASE_DIR = Path(__file__).parent.resolve()

YAML_PATH = BASE_DIR / "chat.yml"
DOCKER_DIR = BASE_DIR / "../chat"
DOCKERFILE = DOCKER_DIR / "chat_server.Dockerfile"

HOST_PROJECT_PATH = DOCKER_DIR
CONTAINER_PROJECT_PATH = "/app"

IMAGE = "chat_server:latest"
CONTAINER_NAME = "chat_server"


def run_command(cmd, ignore_errors=False):
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        if not ignore_errors:
            raise


with open(YAML_PATH) as f:
    config = yaml.safe_load(f)

CHAT_HOST_PORT = config["CHAT_HOST_PORT"]

run_command([
    "docker", "build",
    "-t", IMAGE,
    "-f", str(DOCKERFILE),
    str(DOCKER_DIR)
])

run_command(
    ["docker", "rm", "-f", CONTAINER_NAME],
    ignore_errors=True
)

run_command([
    "docker", "run",
    "-d",
    "-p", f"{CHAT_HOST_PORT}:8000/udp",
    "--name", CONTAINER_NAME,
    IMAGE
])
