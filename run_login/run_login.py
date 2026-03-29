import subprocess
from pathlib import Path

import yaml

BASE_DIR = Path(__file__).parent.resolve()

YAML_PATH = BASE_DIR / "login.yml"
DOCKER_DIR = BASE_DIR / "../loginserver"
DOCKERFILE = DOCKER_DIR / "login_server.Dockerfile"
CERTIFICATE_PATH = DOCKER_DIR / "wrappers/certificate"

HOST_PROJECT_PATH = DOCKER_DIR
CONTAINER_PROJECT_PATH = "/app"

with open(YAML_PATH) as f:
    config = yaml.safe_load(f)

LOGIN_HOST_PORT = config["LOGIN_HOST_PORT"]
LOGIN_HOST_IP = config["LOGIN_HOST_IP"]
LOAD_BALANCER = config["LOAD_BALANCER"]
GAME_SERVER_1 = config["GAME_SERVER_1"]
GAME_SERVER_2 = config["GAME_SERVER_2"]
GAME_SERVER_3 = config["GAME_SERVER_3"]
GAME_SERVER_4 = config["GAME_SERVER_4"]

IMAGE = "login_server:latest"
CONTAINER_NAME = "login_server"


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
    "-p", f"{LOGIN_HOST_PORT}:8050/udp",
    "--name", CONTAINER_NAME,
    "-e", f"LOGIN_SERVER_PORT={LOGIN_HOST_PORT}",
    "-e", f"LOGIN_SERVER_IP={LOGIN_HOST_IP}",
    "-e", f"LOAD_BALANCER={LOAD_BALANCER}",
    "-e", f"GAME_SERVER_1={GAME_SERVER_1}",
    "-e", f"GAME_SERVER_2={GAME_SERVER_2}",
    "-e", f"GAME_SERVER_3={GAME_SERVER_3}",
    "-e", f"GAME_SERVER_4={GAME_SERVER_4}",
    IMAGE
])
