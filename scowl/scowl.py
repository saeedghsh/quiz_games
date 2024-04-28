"""SCOWL (Spell Checker Oriented Word Lists) word list"""

from typing import List


def load_word_list(dict_name: str = "en_US") -> List[str]:
    # pylint: disable=C0116 missing-function-docstring

    file_name = {
        "en_US": "en_US-large.txt",
        "en_CA": "en_CA-large.txt",
        "en_AU": "en_AU-large.txt",
    }[dict_name]
    with open("scowl/" + file_name, encoding="utf-8", mode="r") as file:
        words = [line.strip() for line in file]
    return words
