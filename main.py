"""Entry point for the game"""

import os
import sys
import argparse
from typing import Sequence
from scowl import scowl
from countdown.letter_countdown import (
    LetterCountdown,
    print_optimal_solution,
    print_results,
)
from countdown.word_corpus import WordCorpus
from utilities.terminal import move_cursor_up, clear_line_content, timer


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
    parser = argparse.ArgumentParser(description="Hornet Field entry point")
    parser.add_argument(
        "-n",
        "--number-of-letters",
        default=9,
        type=int,
        help="Number of letters to be selected.",
    )
    parser.add_argument(
        "-t",
        "--timer",
        default=30,
        type=int,
        help="Countdown timer in seconds.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str]):
    # pylint: disable=missing-function-docstring
    args = _parse_arguments(argv)
    word_corpus = WordCorpus(word_corpus_loader=scowl.load_word_list)
    letter_countdown = LetterCountdown(word_corpus, args.number_of_letters)

    while True:
        letter_countdown.select_letters()
        timer(seconds=args.timer)
        responses = letter_countdown.get_user_response()
        print_results(responses, letter_countdown)
        print_optimal_solution(letter_countdown)
        if not _keep_playing():
            break

    return os.EX_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
