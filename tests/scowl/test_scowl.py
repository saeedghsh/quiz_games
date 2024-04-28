# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring

import pytest
from scowl.scowl import load_word_list


def test_load_word_list(mocker):
    mocker.patch("builtins.open", mocker.mock_open(read_data="word1\nword2\nword3"))
    words = load_word_list()
    assert words == ["word1", "word2", "word3"]


def test_load_word_list_different_dict(mocker):
    mocker.patch("builtins.open", mocker.mock_open(read_data="word4\nword5\nword6"))
    words = load_word_list("en_CA")
    assert words == ["word4", "word5", "word6"]


if __name__ == "__main__":
    pytest.main()
