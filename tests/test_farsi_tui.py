"""Play complete terminal rounds to cover language selection and replay."""

import pytest

from main import _parse_arguments, main


def test_language_argument_defaults_and_validation():
    assert _parse_arguments(["countdown-words"]).language == "en"
    assert _parse_arguments(["countdown-words", "--language", "fa"]).language == "fa"
    with pytest.raises(SystemExit):
        _parse_arguments(["countdown-words", "--language", "unknown"])


def test_complete_farsi_rounds_and_normalized_score(monkeypatch, capsys):
    letters = iter("کتابها" * 2)
    answers = iter(["ص", "صامت", "م", "c", "ص", "v", "كِتاب‌ها", "", "بله",
                    "c", "ص", "مصوت", "صامت", "c", "v", "", "خیر"])
    prompts = []

    def respond(prompt):
        prompts.append(prompt)
        return next(answers)

    monkeypatch.setattr("builtins.input", respond)
    monkeypatch.setattr("random.choices", lambda *args, **kwargs: [next(letters)])
    assert main(["countdown-words", "--language", "fa", "-n", "6", "-t", "0"]) == 0
    output = capsys.readouterr().out
    assert "امتیاز: 6" in output
    assert "زمان تمام شد" in output
    assert "بلندترین واژه‌ها" in output
    assert sum("مصوت" in prompt for prompt in prompts) == 12
    assert all("Vowel or consonant" not in prompt for prompt in prompts)


@pytest.mark.parametrize("choice,kind", [("م", "v"), ("مصوت", "v"), ("V", "v"),
                                         ("ص", "c"), ("صامت", "c"), ("C", "c")])
def test_farsi_tui_choice_reaches_correct_pool(monkeypatch, choice, kind):
    from countdown.farsi import FARSI_ALPHABET, FARSI_VOWELS, normalize_farsi
    from countdown.letter_countdown import LetterCountdown
    from countdown.word_corpus import WordCorpus

    game = LetterCountdown(WordCorpus(
        lambda: ["کتاب"], alphabet=FARSI_ALPHABET, vowels=FARSI_VOWELS,
        normalizer=normalize_farsi, language="fa",
    ))
    answers = iter(["invalid", choice])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    drawn = []
    monkeypatch.setattr(game, "draw_letter", lambda selected: drawn.append(selected) or "ا")
    assert game.select_letter() == "ا"
    assert drawn == [kind]


def test_english_terminal_still_plays(monkeypatch, capsys):
    letters = iter("cat")
    answers = iter(["c", "v", "c", "cat", "", "n"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    monkeypatch.setattr("random.choices", lambda *args, **kwargs: [next(letters)])
    assert main(["countdown-words", "-n", "3", "-t", "0"]) == 0
    assert "'cat' is correct! 3 points!" in capsys.readouterr().out
