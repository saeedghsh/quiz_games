"""Word quiz"""

# pylint: disable=C0115 missing-class-docstring
# pylint: disable=C0116 missing-function-docstring

from collections import Counter
import string
from typing import Callable, List, Dict


class WordCorpus:
    def __init__(
        self, word_corpus_loader: Callable, *, alphabet: str = string.ascii_lowercase,
        vowels: str = "aeiou", normalizer: Callable[[str], str] = str,
        ignored_characters: str = "", language: str = "en",
    ) -> None:
        self.language = language
        self.alphabet = list(alphabet)
        self._normalizer = normalizer
        self._ignored_characters = str.maketrans("", "", ignored_characters)
        self._vowels = list(vowels)
        self._consonants = [letter for letter in alphabet if letter not in self._vowels]
        self._corpus = word_corpus_loader()
        self._assert_non_empty_corpus()
        self._word_keys = {self.tile_text(word) for word in self._corpus}
        self._letter_distribution = self._get_letter_distribution()

    def normalize(self, word: str) -> str:
        """Canonical spelling for this language, retaining display word boundaries."""
        return self._normalizer(word)

    def tile_text(self, word: str) -> str:
        """Letters that consume tiles; formatting marks never earn points."""
        return self.normalize(word).translate(self._ignored_characters)

    def word_length(self, word: str) -> int:
        return len(self.tile_text(word))

    @property
    def draw_kinds(self) -> tuple[str, ...]:
        return ("v", "c") if self._vowels else ("letter",)

    @property
    def corpus(self) -> List[str]:
        self._assert_non_empty_corpus()
        return self._corpus

    def _assert_non_empty_corpus(self):
        if not self._corpus:
            raise ValueError("Cannot operate with an empty corpus.")

    @property
    def letter_distribution(self) -> Dict[str, float]:
        return self._letter_distribution

    @property
    def consonants(self) -> List[str]:
        return self._consonants

    @property
    def vowels(self) -> List[str]:
        return self._vowels

    def _get_letter_distribution(self) -> Dict[str, float]:
        distribution = dict(Counter(letter for word in self.corpus for letter in self.tile_text(word)))
        return distribution

    def is_valid_word(self, word: str) -> bool:
        return self.tile_text(word) in self._word_keys
