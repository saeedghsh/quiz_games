"""Exercise browser round transitions against the real shared Python engine."""

import json

import pytest

from countdown.browser import BrowserGame
from countdown.number_countdown import NumberRound, evaluate_expression, solve_number_round
from countdown.word_corpus import WordCorpus


@pytest.fixture
def game():
    return BrowserGame(WordCorpus(lambda: ["cat", "act", "at", "dog", "a"]))


def test_word_round_scoring_solver_and_reset(game, monkeypatch):
    game.new_round(letter_count=3)
    letters = iter("cat")
    monkeypatch.setattr(game.words, "draw_letter", lambda kind: next(letters))
    for _ in range(3):
        game.draw("c")
    assert game.state["phase"] == "playing"
    assert game.state["tiles"] == list("cat")
    result = game.submit("CAT at cat, dog aaaa")["result"]
    assert result["score"] == 3
    assert result["answers"] == [
        {"word": "cat", "valid": True}, {"word": "at", "valid": True},
        {"word": "dog", "valid": False}, {"word": "aaaa", "valid": False},
    ]
    assert set(game.solve()["words"]) == {"cat", "act"}
    assert game.new_round()["tiles"] == []
    assert game.state["result"] is None


def test_fill_uses_weighted_engine_draw(game):
    game.new_round(letter_count=6)
    game.draw("v")
    assert game.state["tiles"][0] in game.corpus.vowels
    assert len(game.fill()["tiles"]) == 6
    assert game.state["phase"] == "playing"


def test_numbers_invalid_answer_can_be_corrected(game, monkeypatch):
    monkeypatch.setattr("countdown.browser.draw_number_round", lambda count: NumberRound((25, 4, 3, 2, 7, 8), 100))
    game.new_round(mode="numbers")
    assert game.submit("25 * 25")["error"]
    assert game.state["phase"] == "playing"
    assert game.submit("__import__('os')")["error"]
    result = game.submit("25 * 4")["result"]
    assert result["value"] == 100
    assert result["score"] == 10
    assert result["distance"] == 0


def test_solver_output_is_valid_for_drawn_tiles():
    result = solve_number_round([25, 4, 3], 103, time_limit_seconds=1)
    assert result.is_complete
    assert result.best_distance == 0
    for expression in result.expressions:
        evaluation = evaluate_expression(expression, [25, 4, 3])
        assert evaluation.is_valid
        assert evaluation.value == 103


def test_number_solver_is_shared_and_cached(game, monkeypatch):
    result = solve_number_round([25, 4], 100, time_limit_seconds=1)
    calls = []

    def solver(numbers, target, time_limit_seconds):
        calls.append((numbers, target, time_limit_seconds))
        return result

    monkeypatch.setattr("countdown.browser.solve_number_round", solver)
    game.new_round(mode="numbers")
    game.submit("")
    assert game.solve()["best_value"] == 100
    game.solve()
    assert len(calls) == 1
    assert calls[0][2] == 3


@pytest.mark.parametrize("method,args", [("draw", ("v",)), ("fill", ()), ("submit", ("cat",)), ("solve", ())])
def test_round_must_be_started(game, method, args):
    with pytest.raises(ValueError):
        getattr(game, method)(*args)


@pytest.mark.parametrize("args", [{"mode": "bad"}, {"letter_count": 0}, {"big_count": 5}])
def test_invalid_settings(game, args):
    with pytest.raises(ValueError):
        game.new_round(**args)


def test_skip_and_dispatch_allowlist(game):
    state = json.loads(game.dispatch('{"action":"new","args":{"mode":"numbers"}}'))
    assert len(state["tiles"]) == 6
    assert game.submit("")["result"]["score"] == 0
    with pytest.raises(ValueError, match="Unknown game action"):
        game.dispatch('{"action":"__init__"}')


def test_reveal_and_extra_draw_are_guarded(game):
    game.new_round()
    with pytest.raises(ValueError):
        game.solve()
    game.fill()
    with pytest.raises(ValueError):
        game.draw("v")


def test_farsi_round_scores_and_language_switch_reset(game, monkeypatch):
    english = game.corpus
    state = json.loads(game.dispatch('{"action":"new","args":{"language":"fa","letter_count":6}}'))
    assert state["language"] == "fa"
    assert state["draw_kinds"] == ["letter"]
    with pytest.raises(ValueError):
        game.draw("v")
    letters = iter("کتابها")
    monkeypatch.setattr(game.words, "draw_letter", lambda kind: next(letters))
    game.fill()
    result = game.submit("كِتاب‌ها، كتاب، cat")["result"]
    assert result["score"] == 6
    assert result["answers"] == [
        {"word": "کتاب‌ها", "valid": True}, {"word": "کتاب", "valid": True},
        {"word": "cat", "valid": False},
    ]
    solutions = game.solve()
    assert solutions["length"] <= 6
    assert all(game.words.is_response_valid(word) for word in solutions["words"])
    assert game.new_round(language="en")["tiles"] == []
    assert game.corpus is english
    assert game.solutions is None
    assert game.state["result"] is None
    assert game.new_round(mode="numbers", language="fa")["language"] == "en"


def test_unknown_language_does_not_change_round(game):
    game.new_round()
    game.draw("v")
    before = list(game.state["tiles"])
    with pytest.raises(ValueError, match="Farsi"):
        game.new_round(language="xx")
    assert game.state["tiles"] == before
