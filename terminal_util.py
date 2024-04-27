# pylint: disable=C0116 missing-function-docstring
# pylint: disable=C0114 missing-module-docstring
import sys
import time


def move_cursor_up(n: int):
    sys.stdout.write(f"\033[{n}A")


def clear_line_content():
    sys.stdout.write("\033[K")


def timer(seconds: int):
    signs = ["-", "\\", "|", "/"]
    for i in range(seconds):
        print(signs[i % len(signs)], f"\t{seconds-i} seconds left")
        time.sleep(1)
        if i < seconds - 1:
            move_cursor_up(1)
    move_cursor_up(1)
    clear_line_content()
    print("Times up!\n")
