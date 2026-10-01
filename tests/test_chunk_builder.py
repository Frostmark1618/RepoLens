from pathlib import Path
from tempfile import TemporaryDirectory

from ingestion.chunk_builder import (
    build_file_chunks,
    build_repository_chunks,
    save_repository_chunks,
)
from ingestion.file_filter import collect_files


def main():
    with TemporaryDirectory() as temp_dir:
        repository_path = Path(temp_dir)
        file_path = repository_path / "example.py"

        file_content = (
            "def hello():\n"
            "    return 'hello'\n"
        )

        file_path.write_text(
            file_content,
            encoding="utf-8",
        )

        chunks = build_file_chunks(
            str(repository_path),
            str(file_path),
        )

        assert len(chunks) == 1

        chunk = chunks[0]

        assert chunk["file"] == "example.py"
        assert chunk["extension"] == ".py"
        assert chunk["start_line"] == 1
        assert chunk["end_line"] == 2
        assert chunk["content"] == file_content.rstrip("\n")



        multi_line_content = (
            "line 1\n"
            "line 2\n"
            "line 3\n"
            "line 4\n"
            "line 5\n"
        )

        multi_line_file = (
            repository_path / "multi_line.py"
        )

        multi_line_file.write_text(
            multi_line_content,
            encoding="utf-8",
        )

        chunks = build_file_chunks(
            str(repository_path),
            str(multi_line_file),
            chunk_size=2,
        )

        assert len(chunks) == 3

        assert chunks[0]["start_line"] == 1
        assert chunks[0]["end_line"] == 2
        assert chunks[0]["content"] == (
            "line 1\nline 2"
        )

        assert chunks[1]["start_line"] == 3
        assert chunks[1]["end_line"] == 4
        assert chunks[1]["content"] == (
            "line 3\nline 4"
        )

        assert chunks[2]["start_line"] == 5
        assert chunks[2]["end_line"] == 5
        assert chunks[2]["content"] == "line 5"

        repository_chunks = build_repository_chunks(
            str(repository_path),
            [
                str(file_path),
                str(multi_line_file),
            ],
            chunk_size=2,
        )

        assert len(repository_chunks) == 4

        assert (
            repository_chunks[0]["file"]
            == "example.py"
        )

        assert (
            repository_chunks[1]["file"]
            == "multi_line.py"
        )

        assert (
            repository_chunks[2]["file"]
            == "multi_line.py"
        )

        relevant_files = collect_files(
            "artifacts/repositories/requests"
        )

        relevant_file_chunks = build_repository_chunks(
            "artifacts/repositories/requests",
            [
                str(file_path)
                for file_path in relevant_files
            ],
            chunk_size=50,
        )

        assert len(relevant_files) > 0
        assert len(relevant_file_chunks) > 0

        for chunk in relevant_file_chunks:
            assert chunk["file"]
            assert chunk["extension"]
            assert chunk["start_line"] >= 1
            assert chunk["end_line"] >= chunk["start_line"]
            assert chunk["content"].strip()



            output_path = (
            repository_path / "repository_chunks.json"
        )

        save_repository_chunks(
            repository_chunks,
            str(output_path),
        )

        assert output_path.exists()
        assert output_path.is_file()

        saved_content = output_path.read_text(
            encoding="utf-8"
        )

        assert '"file": "example.py"' in saved_content
        assert '"extension": ".py"' in saved_content







    print("Chunk builder verification passed.")
    print(f"Chunks: {len(chunks)}")


if __name__ == "__main__":
    main()