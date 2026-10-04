"""Reproduce the bundled word list from the pinned Lilak checkout (no network)."""

import argparse
import hashlib
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from countdown.farsi import FARSI_ALPHABET, normalize_farsi


def import_dictionary(source: Path, output: Path) -> None:
    """Extract standalone lexicon entries; do not expand Hunspell affix rules."""
    data = source.read_bytes()
    if hashlib.sha256(data).hexdigest() != SOURCE_SHA256:
        raise ValueError("Use the Lilak lexicon revision recorded in countdown/data/NOTICE.txt.")
    words = set()
    alphabet = set(FARSI_ALPHABET)
    for line in data.decode("utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        word = normalize_farsi(line.split(",", 1)[0]).strip("\u200c")
        letters = word.replace("\u200c", "")
        if letters and set(letters) <= alphabet:
            words.add(word)
    output.write_text("\n".join(sorted(words)) + "\n", encoding="utf-8")


SOURCE_SHA256 = "4eeb621442cf38d6d9aac2923daced2b8ae17c770773a7260a02f3c3957daff6"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Path to Lilak src/data/lexicon")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    import_dictionary(args.source, args.output)
