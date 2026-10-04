# pylint: disable=C0116 missing-function-docstring
# pylint: disable=C0114 missing-module-docstring
import sys
import time


def move_cursor_up(n: int):
    sys.stdout.write(f"\033[{n}A")


def clear_line_content():
    sys.stdout.write("\033[K")


def timer(seconds: int, language: str = "en"):
    signs = ["-", "\\", "|", "/"]
    for i in range(seconds):
        remaining = f"\t{seconds-i} ثانیه باقی مانده" if language == "fa" else f"\t{seconds-i} seconds left"
        print(signs[i % len(signs)], remaining)
        time.sleep(1)
        if i < seconds - 1:
            move_cursor_up(1)
    move_cursor_up(1)
    clear_line_content()
    print("زمان تمام شد!\n" if language == "fa" else "Times up!\n")
