import subprocess
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()


def run_script(script_path):
    """Run a Python script and raise if it fails."""
    print(f"Running {script_path.name}...")
    subprocess.run(["python", str(script_path)], check=True)
    print(f"{script_path.name} finished.\n")


if __name__ == "__main__":
    # Paths to each service's run script
    scripts = [
        BASE_DIR.parent / "run_game" / "run_game.py",
        BASE_DIR.parent / "run_load_balancer" / "run_load_balancer.py",
        BASE_DIR.parent / "run_login" / "run_login.py",
        BASE_DIR.parent / "run_chat" / "run_chat.py",
    ]

    for script in scripts:
        run_script(script)
        time.sleep(1)  # small delay between each script

    print("All services deployed successfully!")
