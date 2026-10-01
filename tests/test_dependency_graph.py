from pathlib import Path

from ingestion.dependency_graph import build_dependency_edges


def test_relative_import_without_module_is_resolved(tmp_path: Path):
    pkg = tmp_path / "pkg"
    sub = pkg / "sub"
    sub.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "a.py").write_text("from . import b\n", encoding="utf-8")
    (pkg / "b.py").write_text("VALUE = 1\n", encoding="utf-8")
    (sub / "__init__.py").write_text("", encoding="utf-8")
    (sub / "a.py").write_text("from . import b\n", encoding="utf-8")
    (sub / "b.py").write_text("VALUE = 2\n", encoding="utf-8")

    edges = build_dependency_edges(str(tmp_path))
    assert {(e["source"], e["target"]) for e in edges} == {
        ("pkg/a.py", "pkg/b.py"),
        ("pkg/sub/a.py", "pkg/sub/b.py"),
    }


def test_parent_relative_import_is_resolved(tmp_path: Path):
    pkg = tmp_path / "pkg"
    sub = pkg / "sub"
    sub.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "b.py").write_text("VALUE = 1\n", encoding="utf-8")
    (sub / "__init__.py").write_text("", encoding="utf-8")
    (sub / "a.py").write_text("from .. import b\n", encoding="utf-8")

    edges = build_dependency_edges(str(tmp_path))
    assert any(
        e["source"] == "pkg/sub/a.py" and e["target"] == "pkg/b.py"
        for e in edges
    )


def test_src_layout_resolves_absolute_and_relative_imports(tmp_path: Path):
    src = tmp_path / "src" / "app"
    src.mkdir(parents=True)
    (src / "__init__.py").write_text("", encoding="utf-8")
    (src / "service.py").write_text("from . import models\n", encoding="utf-8")
    (src / "models.py").write_text("VALUE = 1\n", encoding="utf-8")

    edges = build_dependency_edges(str(tmp_path))
    assert any(
        e["source"] == "src/app/service.py"
        and e["target"] == "src/app/models.py"
        for e in edges
    )


def test_duplicate_short_module_names_are_not_guessed(tmp_path: Path):
    left = tmp_path / "left"
    right = tmp_path / "right"
    left.mkdir()
    right.mkdir()
    for pkg in (left, right):
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        (pkg / "utils.py").write_text("VALUE = 1\n", encoding="utf-8")

    (tmp_path / "consumer.py").write_text(
        "import utils\n",
        encoding="utf-8",
    )

    edges = build_dependency_edges(str(tmp_path))
    assert not any(
        e["source"] == "consumer.py" and e["target"].endswith("/utils.py")
        for e in edges
    )


def test_package_init_and_alias_imports_resolve(tmp_path: Path):
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("from . import b as beta\n", encoding="utf-8")
    (pkg / "a.py").write_text("import pkg.b as beta\n", encoding="utf-8")
    (pkg / "b.py").write_text("VALUE = 1\n", encoding="utf-8")

    edges = build_dependency_edges(str(tmp_path))
    pairs = {(e["source"], e["target"]) for e in edges}
    assert ("pkg/__init__.py", "pkg/b.py") in pairs
    assert ("pkg/a.py", "pkg/b.py") in pairs
