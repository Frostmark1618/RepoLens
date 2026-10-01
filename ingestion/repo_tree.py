from pathlib import Path


def build_file_tree(repository_path: str) -> dict:
    """
    Build a nested file tree for a repository.

    Directories contain nested dictionaries.
    Files are represented by their names.
    """

    root = Path(repository_path)

    if not root.exists():
        raise FileNotFoundError(
            f"Repository path does not exist: {repository_path}"
        )

    if not root.is_dir():
        raise NotADirectoryError(
            f"Repository path is not a directory: {repository_path}"
        )

    def build_tree(current_path: Path) -> dict:
        tree = {}

        for path in sorted(
            current_path.iterdir(),
            key=lambda item: (item.is_file(), item.name.lower()),
        ):
            if path.is_dir():
                if path.name == ".git":
                    continue

                tree[path.name] = build_tree(path)

            else:
                tree[path.name] = None

        return tree

    return {
        root.name: build_tree(root)
    }


def print_file_tree(tree: dict, indent: int = 0) -> None:
    """
    Print a nested file tree in a readable format.
    """

    for name, children in tree.items():

        print(" " * indent + name)

        if children is not None:
            print_file_tree(
                children,
                indent + 2,
            )


if __name__ == "__main__":

    repository_path = (
        "artifacts/repositories/requests"
    )

    try:

        tree = build_file_tree(
            repository_path
        )

        print("Repository file tree:\n")

        print_file_tree(tree)

    except Exception as error:

        print(f"Error: {error}")