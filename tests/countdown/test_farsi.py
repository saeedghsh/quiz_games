"""Farsi orthography, repeated tiles, normalized scores, and real dictionary."""

from collections import Counter

import pytest

from countdown.farsi import FARSI_ALPHABET, farsi_corpus, normalize_farsi
from countdown.letter_countdown import LetterCountdown
from countdown.word_corpus import WordCorpus


@pytest.fixture
def game():
    corpus = WordCorpus(
        lambda: ["کتاب", "کتاب‌ها", "باب", "آب", "بار"],
        alphabet=FARSI_ALPHABET, vowels="", normalizer=normalize_farsi,
        ignored_characters="\u200c", language="fa",
    )
    return LetterCountdown(corpus)


@pytest.mark.parametrize("entered,canonical", [
    ("كِتاب", "کتاب"), ("علي", "علی"), ("على", "علی"),
    ("کـتاب", "کتاب"), ("ﻛﺘﺎﺏ", "کتاب"), ("ا\u0653ب", "آب"),
])
def test_keyboard_and_unicode_normalization(entered, canonical):
    assert normalize_farsi(entered) == canonical


def test_half_space_and_diacritics_do_not_consume_tiles_or_score(game):
    game.letters = list("كتابها")
    for answer in ("کتاب‌ها", "كتابها", "کِتاب‌ها"):
        assert game.is_response_valid(answer)
        assert game.score_response(answer) == 6
    assert game.optimal_solutions() == ["کتاب‌ها"]
    assert "\u200c" not in game.word_corpus.letter_distribution
    assert game.word_corpus.letter_distribution == dict(Counter("کتابکتابهابابآببار"))


def test_distinct_letters_repeated_tiles_and_spaces(game):
    game.letters = list("بار")
    assert not game.is_response_valid("باب")
    assert not game.is_response_valid("آب")
    assert not game.is_response_valid("با ر")
    assert game.score_response("باب") == 0
    game.letters = list("باب")
    assert game.score_response("باب") == 3
    assert "باب" in game.optimal_solutions()


def test_farsi_draws_only_written_letters(game):
    assert game.word_corpus.draw_kinds == ("letter",)
    for _ in range(50):
        assert game.draw_letter() in FARSI_ALPHABET
    with pytest.raises(ValueError):
        game.draw_letter("v")


def test_bundled_dictionary_works_outside_repo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    corpus = farsi_corpus()
    assert len(corpus.corpus) == 85705
    for word in ("کتاب", "سلام", "خانه", "کتابخانه", "آب", "فارسی"):
        assert corpus.is_valid_word(word)
    assert not corpus.is_valid_word("سلامxyz")
    assert all(set(corpus.tile_text(word)) <= set(FARSI_ALPHABET) for word in corpus.corpus)
    assert all(corpus.tile_text(word) for word in corpus.corpus)
