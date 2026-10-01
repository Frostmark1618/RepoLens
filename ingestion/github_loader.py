from pathlib import Path
import re
import subprocess
from urllib.parse import urlparse

from config.settings import REPOSITORIES_DIR


def clone_repository(repo_url: str, repository_name: str) -> Path:
    """
    Clone a public GitHub repository into RepoLens storage.

    Args:
        repo_url: Public GitHub repository URL.
        repository_name: Name of the local repository folder.

    Returns:
        Path to the cloned repository.

    Raises:
        ValueError: If the URL or repository name is empty.
        RuntimeError: If the destination already exists or Git cloning fails.
    """

    repo_url = repo_url.strip()
    repository_name = repository_name.strip()

    if not repo_url:
        raise ValueError("GitHub repository URL cannot be empty.")

    if not repository_name:
        raise ValueError("Repository name cannot be empty.")

    parsed = urlparse(repo_url)
    if parsed.scheme != "https" or parsed.netloc.lower() != "github.com":
        raise ValueError(
            "Only public HTTPS GitHub repository URLs are supported."
        )

    if not parsed.path.strip("/") or not parsed.path.rstrip("/").endswith(".git") and parsed.path.strip("/").count("/") != 1:
        raise ValueError("Invalid GitHub repository URL.")

    if (
        repository_name in {".", ".."}
        or not re.fullmatch(r"[A-Za-z0-9._-]+", repository_name)
    ):
        raise ValueError("Invalid repository name.")

    destination_path = REPOSITORIES_DIR / repository_name

    if destination_path.exists():
        raise RuntimeError(
            f"Repository already exists: {destination_path}"
        )

    REPOSITORIES_DIR.mkdir(parents=True, exist_ok=True)

    try:
        subprocess.run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--",
                repo_url,
                str(destination_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

    except subprocess.CalledProcessError as error:
        message = error.stderr.strip() or "Unknown Git error."

        raise RuntimeError(
            f"Failed to clone repository: {message}"
        ) from error

    return destination_path


if __name__ == "__main__":
    test_url = "https://github.com/psf/requests.git"
    test_repository_name = "requests"

    try:
        repository_path = clone_repository(
            test_url,
            test_repository_name,
        )

        print("Repository cloned successfully.")
        print(f"Location: {repository_path}")

    except Exception as error:
        print(f"Error: {error}")