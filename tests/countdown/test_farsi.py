"""Farsi orthography, repeated tiles, normalized scores, and real dictionary."""

from collections import Counter

import pytest

from countdown.farsi import FARSI_ALPHABET, FARSI_VOWELS, farsi_corpus, normalize_farsi
from countdown.letter_countdown import LetterCountdown
from countdown.word_corpus import WordCorpus


@pytest.fixture
def game():
    corpus = WordCorpus(
        lambda: ["کتاب", "کتاب‌ها", "باب", "آب", "بار"],
        alphabet=FARSI_ALPHABET, vowels=FARSI_VOWELS, normalizer=normalize_farsi,
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
    assert game.word_corpus.draw_kinds == ("v", "c")
    for _ in range(50):
        assert game.draw_letter() in FARSI_ALPHABET
        assert game.draw_letter("v") in FARSI_VOWELS
        assert game.draw_letter("c") in set(FARSI_ALPHABET) - set(FARSI_VOWELS)
    with pytest.raises(ValueError):
        game.draw_letter("unknown")


def test_farsi_draw_pools_partition_alphabet_and_use_corpus_weights(game, monkeypatch):
    corpus = game.word_corpus
    assert set(corpus.vowels) == set("اآوی")
    assert set(corpus.vowels).isdisjoint(corpus.consonants)
    assert set(corpus.vowels + corpus.consonants) == set(FARSI_ALPHABET)
    calls = []

    def choose(letters, weights, k):
        calls.append((letters, weights, k))
        return [letters[0]]

    monkeypatch.setattr("random.choices", choose)
    game.draw_letter("v")
    game.draw_letter("c")
    for (letters, weights, k), pool in zip(calls, [corpus.vowels, corpus.consonants]):
        assert letters == pool
        assert weights == [corpus.letter_distribution.get(letter, 0) for letter in pool]
        assert k == 1


def test_bundled_dictionary_works_outside_repo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    corpus = farsi_corpus()
    assert corpus.vowels == list(FARSI_VOWELS)
    assert len(corpus.corpus) == 85705
    for word in ("کتاب", "سلام", "خانه", "کتابخانه", "آب", "فارسی"):
        assert corpus.is_valid_word(word)
    assert not corpus.is_valid_word("سلامxyz")
    assert all(set(corpus.tile_text(word)) <= set(FARSI_ALPHABET) for word in corpus.corpus)
    assert all(corpus.tile_text(word) for word in corpus.corpus)
