"""Word quiz"""

# pylint: disable=C0115 missing-class-docstring
# pylint: disable=C0116 missing-function-docstring

from collections import Counter
import string
from typing import Callable, List, Dict


class WordCorpus:
    def __init__(self, word_corpus_loader: Callable) -> None:
        self._vowels = ["a", "e", "i", "o", "u"]
        self._consonants = [l for l in string.ascii_lowercase if l not in self._vowels]
        self._corpus = word_corpus_loader()
        self._assert_non_empty_corpus()
        self._letter_distribution = self._get_letter_distribution()

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
    def consonants(self) -> Dict[str, List[str]]:
        return self._consonants

    @property
    def vowels(self) -> Dict[str, List[str]]:
        return self._vowels

    def _get_letter_distribution(self) -> Dict[str, float]:
        all_letters = [item for sublist in self.corpus for item in sublist]
        distribution = dict(Counter(all_letters))
        return distribution

    def is_valid_word(self, word: str) -> bool:
        return word in self.corpus
