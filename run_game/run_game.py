import subprocess
from pathlib import Path

import yaml

BASE_DIR = Path(__file__).parent.resolve()

YAML_PATH = BASE_DIR / "game.yml"
DOCKER_DIR = BASE_DIR / "../game"
DOCKERFILE = DOCKER_DIR / "game_server.Dockerfile"

HOST_PROJECT_PATH = DOCKER_DIR
CONTAINER_PROJECT_PATH = "/app"

IMAGE = "game_server:latest"


def run_command(cmd, ignore_errors=False):
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        if not ignore_errors:
            raise


with open(YAML_PATH) as f:
    config = yaml.safe_load(f)

ports = config.get("ports", [])
numbers = config.get("numbers", [])

run_command([
    "docker", "build",
    "-t", IMAGE,
    "-f", str(DOCKERFILE),
    str(DOCKER_DIR)
])

for host_port, server_number in zip(ports, numbers):
    container_name = f"game{server_number}"

    run_command(["docker", "rm", "-f", container_name], ignore_errors=True)

    run_command([
        "docker", "run",
        "-d",
        "--name", container_name,
        "-p", f"{host_port}:9000/udp",
        "-e", f"GAME_SERVER_NUMBER={server_number}",
        "-v", f"{HOST_PROJECT_PATH}:{CONTAINER_PROJECT_PATH}",
        IMAGE
    ])
