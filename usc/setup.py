from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def generate_env():
    """Create env file if not existing"""
    env_path = BASE_DIR / ".env"
    env_example_path = BASE_DIR / ".env.example"
    if not env_path.exists():
        content = ""
        with open(env_example_path) as file:
            content = file.read()

        with open(env_path, "w") as file:
            file.write(content)

        print("Creted new ENV file successfully!")
        return

    print("ENV file already exists!")


def create_logs():
    """Create logs directory if not there"""
    log_path = BASE_DIR / "logs"
    if not log_path.exists():
        log_path.mkdir()
        print("Created new log directory successfully!")
        return

    print("Log directory already created")


if __name__ == "__main__":  # pragma: no cover
    generate_env()
    create_logs()
