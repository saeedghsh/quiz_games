"""Ensure the static artifact ships the actual engine and works under a subpath."""

import json
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest

from scripts.build_pages import ROOT, build_pages


def test_build_bundles_canonical_engine_and_dictionary(tmp_path):
    output = tmp_path / "_site"
    build_pages(output)
    for name in ("index.html", "app.js", "worker.js", "styles.css", ".nojekyll", "LICENSE"):
        assert (output / name).exists()
    config = json.loads((output / "runtime-config.json").read_text())
    assert config["pyodide-version"] == "0.28.3"
    with zipfile.ZipFile(output / "python/quiz_games.zip") as archive:
        for name in ("countdown/browser.py", "countdown/number_countdown.py", "scowl/en_US-large.txt"):
            assert archive.read(name) == (ROOT / name).read_bytes()
        archive.extractall(tmp_path / "extracted")
    # Import only from the artifact, with a different current directory.
    result = subprocess.run([
        sys.executable, "-c",
        f"import sys; sys.path.insert(0, {str(tmp_path / 'extracted')!r}); "
        "from countdown.browser import BrowserGame; g = BrowserGame(); "
        "assert len(g.new_round(mode='numbers')['tiles']) == 6; "
        "assert g.corpus.is_valid_word('cat')",
    ], cwd=tmp_path, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    (output / "stale.txt").touch()
    build_pages(output)
    assert not (output / "stale.txt").exists()


def test_build_refuses_source_directory():
    with pytest.raises(ValueError):
        build_pages(ROOT / "web")
