# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=unused-import

from collections import Counter
from unittest.mock import MagicMock
import pytest
from countdown.word_corpus import WordCorpus


def test_word_corpus_initialization_and_properties(mocker):
    mock_loader = mocker.MagicMock(return_value=["apple", "banana", "cherry"])
    corpus = WordCorpus(word_corpus_loader=mock_loader)
    mock_loader.assert_called_once()
    assert corpus.corpus == ["apple", "banana", "cherry"]
    assert set(corpus.vowels) == {"a", "e", "i", "o", "u"}
    assert "a" not in corpus.consonants
    assert "b" in corpus.consonants


def test_letter_distribution(mocker):
    mock_loader = mocker.MagicMock(return_value=["apple", "banana", "cherry"])
    corpus = WordCorpus(word_corpus_loader=mock_loader)
    expected_distribution = dict(Counter("apple" + "banana" + "cherry"))
    assert corpus.letter_distribution == expected_distribution


def test_is_valid_word(mocker):
    mock_loader = mocker.MagicMock(return_value=["apple", "banana", "cherry"])
    corpus = WordCorpus(word_corpus_loader=mock_loader)
    assert corpus.is_valid_word("apple") is True
    assert corpus.is_valid_word("orange") is False


def test_error_on_empty_corpus(mocker):
    mock_loader = mocker.MagicMock(return_value=[])
    with pytest.raises(ValueError, match="Cannot operate with an empty corpus."):
        WordCorpus(word_corpus_loader=mock_loader)


if __name__ == "__main__":
    pytest.main()
