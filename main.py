"""Entry point for the game"""

import argparse
import os
import sys
from typing import Sequence

from countdown.letter_countdown import (
    LetterCountdown,
    print_optimal_solution,
    print_results,
)
from countdown.word_corpus import WordCorpus
from scowl import scowl
from utilities.terminal import clear_line_content, move_cursor_up, timer

COMMAND_COUNTDOWN_WORDS = "countdown-words"


def _keep_playing() -> bool:
    while True:
        response = input("Do you want to play more [y/n]? ").lower()
        if response == "y":
            return True
        if response == "n":
            return False
        move_cursor_up(1)
        clear_line_content()


def _parse_arguments(argv: Sequence[str]) -> argparse.Namespace:  # pragma: no cover
    parser = argparse.ArgumentParser(description="Quiz Games entry point")
    subparsers = parser.add_subparsers(dest="command", required=True)

    countdown_words_parser = subparsers.add_parser(
        COMMAND_COUNTDOWN_WORDS,
        help="Play the Countdown words game.",
    )
    countdown_words_parser.add_argument(
        "-n",
        "--number-of-letters",
        default=9,
        type=int,
        help="Number of letters to be selected.",
    )
    countdown_words_parser.add_argument(
        "-t",
        "--timer",
        default=30,
        type=int,
        help="Countdown timer in seconds.",
    )
    return parser.parse_args(argv)


def _play_countdown_words(args: argparse.Namespace) -> int:
    word_corpus = WordCorpus(word_corpus_loader=scowl.load_word_list)
    letter_countdown = LetterCountdown(word_corpus, args.number_of_letters)

    while True:
        letter_countdown.select_letters()
        timer(seconds=args.timer)
        responses = letter_countdown.get_user_response()
        print_results(responses, letter_countdown)
        optimal_solutions = letter_countdown.optimal_solutions()
        print_optimal_solution(optimal_solutions)
        if not _keep_playing():
            break

    return os.EX_OK


def main(argv: Sequence[str]) -> int:
    # pylint: disable=missing-function-docstring
    args = _parse_arguments(argv)

    if args.command == COMMAND_COUNTDOWN_WORDS:
        return _play_countdown_words(args)

    raise ValueError(f"Unrecognized command: {args.command}")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
