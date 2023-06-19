import setup
from setup import generate_env, create_logs


def test_generate_env(tmp_path):

    example_path = tmp_path / ".env.example"
    with open(example_path, "w") as f:
        f.write("test")

    setup.BASE_DIR = tmp_path
    generate_env()

    path = tmp_path / ".env"
    assert path.exists()

    generate_env()
    assert path.exists()


def test_create_logs(tmp_path):

    setup.BASE_DIR = tmp_path

    create_logs()
    path = tmp_path / "logs"
    assert path.exists()

    create_logs()
    assert path.exists()
