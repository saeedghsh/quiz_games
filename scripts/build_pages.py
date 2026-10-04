"""Build a static Pyodide site from the canonical Python sources and dictionary."""

import argparse
import json
from pathlib import Path
import shutil
import tomllib
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def build_pages(output: Path = ROOT / "_site") -> None:
    """Build into a dedicated _site folder, never a source directory."""
    output = output.absolute()
    if output.name != "_site" or output.is_symlink() or output.resolve() in ROOT.parents:
        raise ValueError("Output must be a dedicated directory named _site.")
    if output.exists():
        shutil.rmtree(output)
    shutil.copytree(ROOT / "web", output)
    (output / "python").mkdir()
    with zipfile.ZipFile(output / "python/quiz_games.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for package in ("countdown", "scowl", "utilities"):
            for source in sorted((ROOT / package).glob("*.py")):
                archive.write(source, source.relative_to(ROOT))
        archive.write(ROOT / "scowl/en_US-large.txt", "scowl/en_US-large.txt")
        for source in sorted((ROOT / "countdown/data").glob("*.txt")):
            archive.write(source, source.relative_to(ROOT))
        archive.write(ROOT / "LICENSE", "LICENSE")
    browser = tomllib.loads((ROOT / "pyproject.toml").read_text())["tool"]["quiz-games"]["browser"]
    (output / "runtime-config.json").write_text(json.dumps(browser, indent=2) + "\n")
    shutil.copy2(ROOT / "LICENSE", output / "LICENSE")
    (output / "dictionary").mkdir()
    for name in ("NOTICE.txt", "LICENSE-lilak.txt"):
        shutil.copy2(ROOT / "countdown/data" / name, output / "dictionary" / name)
    (output / ".nojekyll").touch()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "_site")
    build_pages(parser.parse_args().output)
