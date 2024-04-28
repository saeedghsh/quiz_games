# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=redefined-outer-name
# pylint: disable=unused-import
# pylint: disable=protected-access
from collections import Counter
from unittest.mock import patch, MagicMock
import pytest
from countdown.letter_countdown import LetterCountdown
from countdown.word_corpus import WordCorpus


@pytest.fixture
def mock_word_corpus():
    def word_corpus_loader():
        return ["apple", "banana", "cabbage", "door", "zebra"]

    corpus = WordCorpus(word_corpus_loader=word_corpus_loader)
    corpus._vowels = ["a", "e", "i", "o", "u"]
    corpus._consonants = [chr(i) for i in range(97, 123) if chr(i) not in corpus.vowels]
    corpus._letter_distribution = {
        char: 1 for char in corpus.consonants + corpus.vowels
    }
    return corpus


@pytest.fixture
def letter_countdown(mock_word_corpus):
    return LetterCountdown(word_corpus=mock_word_corpus)


def test_empty_letters_error(letter_countdown):
    with pytest.raises(ValueError, match="Set of letters is empty"):
        _ = letter_countdown.letters


def test_set_get_letters(letter_countdown):
    letter_countdown.letters = ["a", "b", "c"]
    assert letter_countdown.letters == ["a", "b", "c"]


def test_reset_letters(letter_countdown):
    letter_countdown.letters = ["a", "b", "c"]
    letter_countdown.reset_letters()
    with pytest.raises(ValueError, match="Set of letters is empty"):
        _ = letter_countdown.letters


def test_select_letter_vowel_or_consonant(mocker, letter_countdown):
    lc = "countdown.letter_countdown.LetterCountdown"
    mocker.patch(f"{lc}.vowel_or_consonant", return_value="v")
    mocker.patch("random.choices", return_value=["e"])
    assert letter_countdown.select_letter() == "e"


def test_select_letters(mocker, letter_countdown):
    lc = "countdown.letter_countdown.LetterCountdown"
    mocker.patch(f"{lc}.vowel_or_consonant", return_value="v")
    mocker.patch("random.choices", return_value=["e"])
    mocker.patch("utilities.terminal.clear_line_content")
    mocker.patch("utilities.terminal.move_cursor_up")
    mocker.patch("builtins.print")
    letter_countdown._number_of_letters = 1
    letter_countdown.select_letters()
    assert letter_countdown.letters == ["e"]


def test_is_allowed(letter_countdown):
    letter_countdown.letters = ["a", "p", "p", "l", "e"]
    assert letter_countdown._is_allowed("apple")
    assert not letter_countdown._is_allowed("apples")


def test_is_response_valid(mocker, letter_countdown):
    mocker.patch.object(letter_countdown, "_is_allowed", return_value=True)
    mocker.patch.object(
        letter_countdown.word_corpus, "is_valid_word", return_value=True
    )
    assert letter_countdown.is_response_valid("apple")


def test_get_user_response(mocker):
    mocker.patch("builtins.input", side_effect=["apple", "banana", ""])
    mocker.patch("utilities.terminal.move_cursor_up")
    mocker.patch("utilities.terminal.clear_line_content")
    mocker.patch("builtins.print")
    assert LetterCountdown.get_user_response() == ["apple", "banana"]


def test_optimal_solutions(mocker, letter_countdown):
    mocker.patch.object(
        letter_countdown, "_is_allowed", side_effect=[False, False, True, False, True]
    )
    sorted_mock = ["zebra", "door", "cabbage", "banana", "apple"]
    mocker.patch("builtins.sorted", return_value=sorted_mock)
    assert letter_countdown.optimal_solutions() == ["cabbage"]


if __name__ == "__main__":
    pytest.main()
