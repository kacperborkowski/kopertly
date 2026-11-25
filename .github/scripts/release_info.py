import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def current_version() -> str:
    pyproject = tomllib.loads((ROOT / "backend" / "pyproject.toml").read_text())
    return pyproject["project"]["version"]


def release_notes(version: str) -> str:
    changelog = (ROOT / "CHANGELOG.md").read_text()
    match = re.search(
        rf"^## \[{re.escape(version)}\][^\n]*\n(.*?)(?=^## \[|^\[[^\]]+\]: |\Z)",
        changelog,
        flags=re.MULTILINE | re.DOTALL,
    )
    if match is None:
        sys.exit(f"CHANGELOG.md nie ma sekcji ## [{version}]")
    return match.group(1).strip()


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "version"
    if command == "version":
        print(current_version())
    elif command == "notes":
        print(release_notes(current_version()))
    else:
        sys.exit(f"Nieznana komenda: {command}")
