import subprocess
from pathlib import Path

import yaml

BASE_DIR = Path(__file__).parent.resolve()

YAML_PATH = BASE_DIR / "load_balancer.yml"
DOCKER_DIR = BASE_DIR / "../loadbalancer"
DOCKERFILE = DOCKER_DIR / "load_balancer.Dockerfile"

HOST_PROJECT_PATH = DOCKER_DIR
CONTAINER_PROJECT_PATH = "/app"

with open(YAML_PATH) as f:
    config = yaml.safe_load(f)

LOAD_BALANCER_HOST_PORT = config["LOAD_BALANCER_HOST_PORT"]

GAME_SERVER_1 = config["GAME_SERVER_1"]
GAME_SERVER_2 = config["GAME_SERVER_2"]
GAME_SERVER_3 = config["GAME_SERVER_3"]
GAME_SERVER_4 = config["GAME_SERVER_4"]

IMAGE = "load_balancer:latest"
CONTAINER_NAME = "load_balancer"


def run_command(cmd, ignore_errors=False):
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        if not ignore_errors:
            raise


run_command([
    "docker", "build",
    "-t", IMAGE,
    "-f", DOCKERFILE,
    DOCKER_DIR
])

run_command(
    ["docker", "rm", "-f", CONTAINER_NAME],
    ignore_errors=True
)

run_command([
    "docker", "run",
    "-d",
    "-p", f"{LOAD_BALANCER_HOST_PORT}:9050/udp",
    "--name", CONTAINER_NAME,
    "-e", f"GAME_SERVER_1={GAME_SERVER_1}",
    "-e", f"GAME_SERVER_2={GAME_SERVER_2}",
    "-e", f"GAME_SERVER_3={GAME_SERVER_3}",
    "-e", f"GAME_SERVER_4={GAME_SERVER_4}",
    "-v", f"{HOST_PROJECT_PATH}:{CONTAINER_PROJECT_PATH}",
    IMAGE
])
