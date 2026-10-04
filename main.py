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
from countdown.number_countdown import play_number_round
from countdown.word_corpus import WordCorpus
from utilities.terminal import clear_line_content, move_cursor_up, timer

COMMAND_COUNTDOWN_WORDS = "countdown-words"
COMMAND_COUNTDOWN_NUMBERS = "countdown-numbers"


def _keep_playing(language: str = "en") -> bool:
    while True:
        prompt = "دوباره بازی می‌کنید؟ [بله/خیر]: " if language == "fa" else "Do you want to play more [y/n]? "
        response = input(prompt).strip().lower()
        if response == "y" or (language == "fa" and response in {"بله", "ب"}):
            return True
        if response == "n" or (language == "fa" and response in {"خیر", "خ"}):
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
        "--language", choices=("en", "fa"), default="en",
        help="Word language: en (English) or fa (Farsi).",
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

    countdown_numbers_parser = subparsers.add_parser(
        COMMAND_COUNTDOWN_NUMBERS,
        help="Play the Countdown numbers game.",
    )
    countdown_numbers_parser.add_argument(
        "-t",
        "--timer",
        default=30,
        type=int,
        help="Countdown timer in seconds.",
    )
    return parser.parse_args(argv)


def _play_countdown_words(args: argparse.Namespace) -> int:
    from scowl import scowl  # pylint: disable=import-outside-toplevel

    if args.language == "fa":
        from countdown.farsi import farsi_corpus

        word_corpus = farsi_corpus()
    else:
        word_corpus = WordCorpus(word_corpus_loader=scowl.load_word_list)
    letter_countdown = LetterCountdown(word_corpus, args.number_of_letters)

    while True:
        letter_countdown.select_letters()
        timer(seconds=args.timer, language=args.language)
        responses = letter_countdown.get_user_response(language=args.language)
        print_results(responses, letter_countdown)
        optimal_solutions = letter_countdown.optimal_solutions()
        print_optimal_solution(optimal_solutions, word_corpus)
        if not _keep_playing(args.language):
            break

    return os.EX_OK


def _play_countdown_numbers(args: argparse.Namespace) -> int:
    while True:
        play_number_round(args.timer)
        if not _keep_playing():
            break

    return os.EX_OK


def main(argv: Sequence[str]) -> int:
    # pylint: disable=missing-function-docstring
    args = _parse_arguments(argv)

    if args.command == COMMAND_COUNTDOWN_WORDS:
        return _play_countdown_words(args)
    if args.command == COMMAND_COUNTDOWN_NUMBERS:
        return _play_countdown_numbers(args)

    raise ValueError(f"Unrecognized command: {args.command}")


def cli() -> int:
    """Installed terminal entry point."""
    return main(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(cli())
