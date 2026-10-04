"""Persian orthography and an offline dictionary for the shared word engine."""

from pathlib import Path
import unicodedata

from countdown.word_corpus import WordCorpus

# Written forms with hamza are separate tiles, as is alef with madda (آ).
FARSI_ALPHABET = "اآبپتثجچحخدذرزژسشصضطظعغفقکگلمنوهیءأإؤئ"
# Gameplay tile pools, rather than a phonetic classification of every use.
FARSI_VOWELS = "اآوی"
_KEYBOARD_VARIANTS = str.maketrans({"ك": "ک", "ي": "ی", "ى": "ی", "ـ": ""})
_OPTIONAL_MARKS = frozenset(chr(code) for code in range(0x064B, 0x0653)) | {"\u0670"}


def normalize_farsi(word: str) -> str:
    """Normalize keyboard/presentation forms without folding distinct letters."""
    word = unicodedata.normalize("NFKC", word).translate(_KEYBOARD_VARIANTS)
    return "".join(char for char in word if char not in _OPTIONAL_MARKS).strip()


def load_farsi_words() -> list[str]:
    """Load the bundled Lilak-derived surface forms, independently of cwd."""
    return (Path(__file__).parent / "data/fa_words.txt").read_text(encoding="utf-8").splitlines()


def farsi_corpus() -> WordCorpus:
    return WordCorpus(
        load_farsi_words, alphabet=FARSI_ALPHABET, vowels=FARSI_VOWELS,
        normalizer=normalize_farsi, ignored_characters="\u200c", language="fa",
    )
