"""JSON interface to the shared engines; no browser or terminal dependencies."""

from dataclasses import asdict
import json
import random

from countdown.letter_countdown import LetterCountdown
from countdown.number_countdown import (
    draw_number_round,
    evaluate_expression,
    score_distance,
    solve_number_round,
)
from countdown.word_corpus import WordCorpus
from scowl.scowl import load_word_list


class BrowserGame:
    """Own a single round, exposing only JSON-compatible state to the web UI."""

    def __init__(self, corpus: WordCorpus | None = None):
        self.corpus = corpus if corpus is not None else WordCorpus(load_word_list)
        self._corpora = {self.corpus.language: self.corpus}
        self.words = LetterCountdown(self.corpus)
        self.number_round = None
        self.state = {"mode": "words", "phase": "idle", "tiles": [], "result": None}
        self.solutions = None

    def new_round(self, mode="words", letter_count=9, big_count=2, language="en"):
        if mode not in {"words", "numbers"}:
            raise ValueError("Choose words or numbers.")
        if type(letter_count) is not int or not 3 <= letter_count <= 12:
            raise ValueError("Choose between 3 and 12 letters.")
        if type(big_count) is not int or not 0 <= big_count <= 4:
            raise ValueError("Choose between 0 and 4 big numbers.")
        if language not in {"en", "fa"}:
            raise ValueError("Choose English (en) or Farsi (fa).")
        language = language if mode == "words" else "en"
        if language not in self._corpora:
            if language == "fa":
                from countdown.farsi import farsi_corpus

                self._corpora[language] = farsi_corpus()
            else:
                self._corpora[language] = WordCorpus(load_word_list)
        self.corpus = self._corpora[language]
        self.words = LetterCountdown(self.corpus, letter_count)
        self.solutions = None
        self.number_round = draw_number_round(big_count) if mode == "numbers" else None
        self.state = {
            "mode": mode,
            "language": language,
            "draw_kinds": self.corpus.draw_kinds,
            "phase": "selecting" if mode == "words" else "playing",
            "letter_count": letter_count,
            "tiles": list(self.number_round.numbers) if self.number_round else [],
            "target": self.number_round.target if self.number_round else None,
            "result": None,
        }
        return self.state

    def draw(self, kind):
        if self.state["phase"] != "selecting":
            raise ValueError("Start a words round before drawing letters.")
        self.state["tiles"].append(self.words.draw_letter(kind))
        self.words.letters = list(self.state["tiles"])
        if len(self.state["tiles"]) == self.state["letter_count"]:
            self.state["phase"] = "playing"
        return self.state

    def fill(self):
        if self.state["phase"] != "selecting":
            raise ValueError("Start a words round before drawing letters.")
        while self.state["phase"] == "selecting":
            kinds = ("v", "c", "c") if self.corpus.draw_kinds == ("v", "c") else ("letter",)
            self.draw(random.choice(kinds))
        return self.state

    def submit(self, answer=""):
        if self.state["phase"] != "playing":
            raise ValueError("Complete the draw before submitting an answer.")
        if not isinstance(answer, str) or len(answer) > 500:
            raise ValueError("Please keep your answer under 500 characters.")
        if self.state["mode"] == "words":
            answers = list(dict.fromkeys(
                self.corpus.normalize(word)
                for word in answer.lower().replace(",", " ").replace("،", " ").split()
            ))
            checked = [
                {"word": word, "valid": self.words.is_response_valid(word)} for word in answers
            ]
            score = max((self.words.score_response(row["word"]) for row in checked), default=0)
            result = {"answers": checked, "score": score, "error": ""}
        else:
            evaluation = evaluate_expression(answer.strip(), self.number_round.numbers)
            # Invalid nonempty declarations can be corrected, as in the TUI.
            if not evaluation.is_valid and answer.strip():
                return {**self.state, "error": evaluation.error}
            distance = (
                abs(self.number_round.target - evaluation.value) if evaluation.is_valid else None
            )
            result = {
                **asdict(evaluation),
                "distance": distance,
                "score": score_distance(distance),
                "answer": answer,
            }
        self.state.update(phase="finished", result=result)
        return self.state

    def solve(self):
        if self.state["phase"] != "finished":
            raise ValueError("Submit or skip the round before revealing solutions.")
        if self.solutions is None:
            if self.state["mode"] == "words":
                words = self.words.optimal_solutions()
                self.solutions = {
                    "words": words, "length": self.corpus.word_length(words[0]) if words else 0,
                }
            else:
                result = solve_number_round(
                    self.number_round.numbers, self.number_round.target, time_limit_seconds=3
                )
                self.solutions = {**asdict(result), "expressions": result.expressions[:2]}
        return self.solutions

    def dispatch(self, request_json: str) -> str:
        """Handle a small allowlisted protocol; user input is always data, never code."""
        request = json.loads(request_json)
        handlers = {
            "new": self.new_round,
            "draw": self.draw,
            "fill": self.fill,
            "submit": self.submit,
            "solve": self.solve,
        }
        action = request.get("action")
        if action not in handlers:
            raise ValueError("Unknown game action.")
        return json.dumps(handlers[action](**request.get("args", {})))
