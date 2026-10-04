"""Word quiz"""

# pylint: disable=C0115 missing-class-docstring
# pylint: disable=C0116 missing-function-docstring

from collections import Counter
import random
from typing import List
from countdown.word_corpus import WordCorpus
from utilities.terminal import move_cursor_up, clear_line_content


class LetterCountdown:
    def __init__(self, word_corpus: WordCorpus, number_of_letters: int = 9) -> None:
        self._word_corpus = word_corpus
        self._number_of_letters = number_of_letters
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
        self._letters = list(self.word_corpus.tile_text("".join(value)))

    def reset_letters(self):
        self.letters = []

    @staticmethod
    def vowel_or_consonant(language: str = "en") -> str:
        """Method to ask user to input letter type, vowel or consonant"""
        prompt = (
            "مصوت (ا، آ، و، ی) یا صامت؟ [v/c یا م/ص]: "
            if language == "fa" else "Vowel or consonant [v/c]? "
        )
        choices = {"v": "v", "c": "c"}
        if language == "fa":
            choices.update({"م": "v", "مصوت": "v", "ص": "c", "صامت": "c"})
        while True:
            letter_type = input(prompt).strip().lower()
            if letter_type in choices:
                return choices[letter_type]
            move_cursor_up(1)
            clear_line_content()

    def select_letter(self) -> str:
        return self.draw_letter(LetterCountdown.vowel_or_consonant(self.word_corpus.language))

    def draw_letter(self, letter_type: str = "letter") -> str:
        """Draw a weighted letter without terminal input (shared by both UIs)."""
        if letter_type == "letter":
            letters = self.word_corpus.alphabet
        elif letter_type not in self.word_corpus.draw_kinds:
            raise ValueError(f"Unrecognized letter type: {letter_type}.")
        elif letter_type == "v":
            letters = self.word_corpus.vowels
        elif letter_type == "c":
            letters = self.word_corpus.consonants
        else:
            raise ValueError(f"Unrecognized letter type: {letter_type}.")
        weights = [self.word_corpus.letter_distribution.get(letter, 0) for letter in letters]
        return random.choices(letters, weights, k=1)[0]  # 'k=1' means one item

    def select_letters(self):
        letters = []
        while len(letters) < self._number_of_letters:
            clear_line_content()
            letter = self.select_letter()
            letters.append(letter)
            clear_line_content()
            label = "حروف انتخاب‌شده" if self.word_corpus.language == "fa" else "Selected letters"
            print(f"{label}: {' '.join(letter.upper() for letter in letters)}")
            if len(letters) < self._number_of_letters:
                move_cursor_up(2)
        self.letters = [letter.lower() for letter in letters]

    def _is_allowed(self, word: str) -> bool:
        counter_word = Counter(self.word_corpus.tile_text("".join(word)))
        counter_allowed_letters = Counter(self.letters)
        for element, count in counter_word.items():
            if counter_allowed_letters[element] < count:
                return False
        return True

    def is_response_valid(self, response: str) -> bool:
        is_allowed = self._is_allowed(list(response))
        is_valid_word = self.word_corpus.is_valid_word(response)
        return is_allowed and is_valid_word

    def score_response(self, response: str) -> int:
        """Score written letters consistently across terminal and browser UIs."""
        return self.word_corpus.word_length(response) if self.is_response_valid(response) else 0

    @staticmethod
    def get_user_response(language: str = "en") -> List[str]:
        responses = []
        prompt = (
            "واژهٔ خود را بنویسید [Enter خالی برای پایان]: " if language == "fa"
            else "Enter your answer [empty-enter to stop]:  "
        )
        while True:
            response = input(prompt).strip().lower()
            if response:
                responses.append(response)
            else:
                break
        move_cursor_up(1)
        clear_line_content()
        print()
        return responses

    def optimal_solutions(self) -> List[str]:
        """Return all words that would get the highest score"""
        sorted_words = sorted(self.word_corpus.corpus, key=self.word_corpus.word_length, reverse=True)
        word_length = None
        result = []
        for word in sorted_words:
            length = self.word_corpus.word_length(word)
            if word_length is not None and length < word_length:
                break
            if self._is_allowed(list(word)):
                result.append(word)
                word_length = length
        return result


def print_results(responses: List[str], letter_countdown: LetterCountdown):
    for response in responses:
        is_valid = letter_countdown.is_response_valid(response)
        score = letter_countdown.score_response(response)
        if letter_countdown.word_corpus.language == "fa":
            correctness = "درست" if is_valid else "نادرست"
            print(f"پاسخ «{response}» {correctness} است! امتیاز: {score}")
        else:
            correctness = "correct" if is_valid else "incorrect"
            print(f"Your answer '{response}' is {correctness}! {score} points!")
    print()


def print_optimal_solution(solutions: List[str], word_corpus: WordCorpus | None = None):
    farsi = word_corpus is not None and word_corpus.language == "fa"
    if solutions:
        length = word_corpus.word_length(solutions[0]) if word_corpus else len(solutions[0])
        print(f"بلندترین واژه‌ها {length} حرف دارند:" if farsi else f"Longest possible word[s] have {length} letters:")
        for w in solutions:
            print(f"\t{w}")
    else:
        print("با این حروف واژه‌ای پیدا نشد!" if farsi else "No word is possible with this combination!")
    print()
