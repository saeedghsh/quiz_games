# Farsi word game

The Python word engine supports Farsi through `countdown.farsi.farsi_corpus()`:

```python
from countdown.farsi import farsi_corpus
from countdown.letter_countdown import LetterCountdown

game = LetterCountdown(farsi_corpus())
game.letters = list("کتابخانه")
assert game.is_response_valid("كتابخانه")
assert game.score_response("کتابخانه") == 8
print(game.optimal_solutions())
```

Farsi draws use the full written alphabet, weighted by letter occurrences in
the dictionary. There is no English-style vowel/consonant split. Each written
letter consumes one tile and earns one point, and repeated letters require
repeated tiles.

Arabic keyboard `ك` and `ي`/`ى` map to Persian `ک` and `ی`. Unicode presentation
forms are normalized. Optional short-vowel marks, shadda, tanwin and tatweel
do not consume tiles. A half-space (`نیم‌فاصله`, U+200C) can be entered or omitted
and never earns a point. Ordinary spaces are still word boundaries.
`آ` and `ا` are distinct tiles; written hamza forms `ء أ إ ؤ ئ` are also
preserved. Visually similar letters such as `س`/`ص` are never conflated.

The bundled 85,705 entries come from a pinned revision of
[Lilak](https://github.com/b00f/lilak), with the upstream attribution and
Apache-2.0 license in `countdown/data/`. These are dictionary surface forms:
proper names and uncommon entries may be accepted, and affixed words are
accepted only when explicitly listed. This is not a full morphological spell
checker. The engine, solver, and scores all use the same normalization rules.
See `countdown/data/NOTICE.txt` for the reproducible import command.
