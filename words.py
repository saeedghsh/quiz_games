"""Word quiz"""

# pylint: disable=C0115 missing-class-docstring
# pylint: disable=C0116 missing-function-docstring

from collections import Counter
import random
import string
from typing import List, Dict

import nltk

from terminal_util import move_cursor_up, clear_line_content


class WordCorpus:
    # TODO: find a better dictionary
    def __init__(self, word_source: str = "unix") -> None:
        self._vowels = ["a", "e", "i", "o", "u"]
        self._consonants = [l for l in string.ascii_lowercase if l not in self._vowels]
        self._corpus = self.get_word_corpus(word_source)
        self._letter_distribution = self._get_letter_distribution()

    @property
    def corpus(self) -> List[str]:
        return self._corpus

    @property
    def letter_distribution(self) -> Dict[str, float]:
        return self._letter_distribution

    @property
    def consonants(self) -> Dict[str, List[str]]:
        return self._consonants

    @property
    def vowels(self) -> Dict[str, List[str]]:
        return self._vowels

    @staticmethod
    def get_word_corpus(source: str = "unix") -> List[str]:
        if source == "nltk":
            nltk.download("words")
            english_word_corpus = nltk.corpus.words.words()
        elif source == "unix":
            with open("/usr/share/dict/words", mode="r", encoding="utf-8") as word_file:
                english_word_corpus = set(word_file.read().split())
        else:
            raise ValueError(
                f"Acceptable word sources are 'unix' and 'nltk'! provided {source}"
            )
        return english_word_corpus

    def _get_letter_distribution(self) -> Dict[str, float]:
        if not self.corpus:
            raise ValueError("Cannot compute letter distribution if corpus is empty")
        all_letters = [item for sublist in self.corpus for item in sublist]
        distribution = dict(Counter(all_letters))
        return distribution

    def is_valid_word(self, word: str) -> bool:
        return word in self.corpus


class WordCountdown:
    def __init__(self, number_of_letters: int = 9, timer: int = 30) -> None:
        self._word_corpus = WordCorpus()
        self._number_of_letters = number_of_letters
        self._timer = timer
        self._letters = []

    @property
    def word_corpus(self) -> WordCorpus:
        return self._word_corpus

    @property
    def letters(self) -> List[str]:
        if not self._letters:
            raise ValueError("Set of letters is empty")
        return self._letters

    @letters.setter
    def letters(self, value: List[str]):
        self._letters = value

    def reset_letters(self):
        self.letters = []

    @property
    def timer(self) -> int:
        return self._timer

    @staticmethod
    def vowel_or_consonant() -> str:
        """Method to ask user to input letter type, vowel or consonant"""
        while True:
            letter_type = input("Vowel or consonant [v/c]? ").lower()
            if letter_type in ["v", "c"]:
                return letter_type
            move_cursor_up(1)
            clear_line_content()

    def select_letter(self) -> str:
        letter_type = WordCountdown.vowel_or_consonant()
        if letter_type == "v":
            letters = self.word_corpus.vowels
        elif letter_type == "c":
            letters = self.word_corpus.consonants
        else:
            raise ValueError(f"Unrecognized letter type: {letter_type}.")
        weights = [self.word_corpus.letter_distribution[letter] for letter in letters]
        return random.choices(letters, weights, k=1)[0]  # 'k=1' means one item

    def select_letters(self):
        letters = []
        while len(letters) < self._number_of_letters:
            clear_line_content()
            letter = self.select_letter()
            letters.append(letter)
            clear_line_content()
            print(f"Selected letters: {' '.join(letter.upper() for letter in letters)}")
            if len(letters) < self._number_of_letters:
                move_cursor_up(2)
        self.letters = [letter.lower() for letter in letters]

    def _is_allowed(self, word: str) -> bool:
        counter_word = Counter(list(word))
        counter_allowed_letters = Counter(self.letters)
        for element, count in counter_word.items():
            if counter_allowed_letters[element] < count:
                return False
        return True

    def is_response_valid(self, response: str) -> bool:
        is_allowed = self._is_allowed(list(response))
        is_valid_word = self.word_corpus.is_valid_word(response)
        return is_allowed and is_valid_word

    @staticmethod
    def get_user_response() -> List[str]:
        responses = []
        while True:
            response = input("Enter your answer [empty-enter to stop]:  ").lower()
            if response:
                responses.append(response)
            else:
                break
        move_cursor_up(1)
        clear_line_content()
        print()
        return responses

    def optimal_solution(self) -> List[str]:
        """Return all words that would get the highest score"""
        sorted_words = sorted(self.word_corpus.corpus, key=len, reverse=True)
        word_length = None
        result = []
        for word in sorted_words:
            if word_length is not None and len(word) < word_length:
                break
            if self._is_allowed(list(word)):
                result.append(word)
                word_length = len(word)
        return result


class Printer:
    @staticmethod
    def print_results(responses: List[str], word_countdown: WordCountdown):
        for response in responses:
            is_valid = word_countdown.is_response_valid(response)
            score = len(response) if is_valid else 0
            correctness = "correct" if is_valid else "incorrect"
            print(f"Your answer '{response}' is {correctness}! {score} points!")
        print()

    @staticmethod
    def print_optimal_solution(word_countdown: WordCountdown):
        longest_possible_words = word_countdown.optimal_solution()
        if longest_possible_words:
            print(
                f"Longest possible word[s] have {len(longest_possible_words[0])} letters:"
            )
            for w in longest_possible_words:
                print(f"\t{w}")
        else:
            print("No word is possible with this combination!")
        print()
