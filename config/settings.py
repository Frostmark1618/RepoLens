from pathlib import Path


# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent


# Repository storage
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
REPOSITORIES_DIR = ARTIFACTS_DIR / "repositories"


# Supported files for Phase 1
SUPPORTED_EXTENSIONS = {
    ".py",
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
}


# Directories that RepoLens should ignore
IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    ".idea",
    ".vscode",
}