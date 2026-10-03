# Quiz Games

Available at: [http://saeed.im/quiz_games/](http://saeed.im/quiz_games/)

## Countdown

<p align="center">
  <img src="https://github.com/saeedghsh/quiz_games/blob/master/images/letter_countdown_01.png" alt="Image 1" width="30%">
  <img src="https://github.com/saeedghsh/quiz_games/blob/master/images/letter_countdown_02.png" alt="Image 2" width="30%">
  <img src="https://github.com/saeedghsh/quiz_games/blob/master/images/letter_countdown_03.png" alt="Image 3" width="30%">
</p>

## Setup with uv

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then:

```bash
uv sync --locked
```

Dependencies and development tools are declared in `pyproject.toml` and locked
in `uv.lock`. The game uses the Python standard library and bundled SCOWL word
lists; NLTK is not needed. Python 3.12 or newer is supported.

## Play in the terminal

```bash
uv run quiz-games countdown-words
uv run quiz-games countdown-words --number-of-letters 9 --timer 30
uv run quiz-games countdown-numbers
```

The original entry point also works: `uv run python main.py countdown-words`.

## Play in the browser

```bash
make serve-pages
```

Open <http://localhost:8000>. Both words and numbers run the same Python engine
locally in your browser through Pyodide, with a responsive web interface,
configurable thinking time, answer validation, scoring, and solver results.
The terminal interface remains available. No Python application server is
required; the first browser load downloads Pyodide from its CDN.

Without Make:

```bash
uv run python scripts/build_pages.py
uv run python -m http.server 8000 --directory _site
```

`_site/` is ready for static hosting, including GitHub Pages. See
[browser architecture and deployment](docs/browser_architecture.md) for details.
The approach follows [Distribution Playground](https://github.com/saeedghsh/distribution_playground/).

## Development

```bash
uv run --locked pytest
make test-browser  # Real browser + Pyodide; needs network access
```

## Laundry List

* [x] turn the current version to a sub-parser `python main.py countdown-words`
* [x] `python main.py countdown-numbers`
* [ ] `python main.py wordle --letter-count=5 --tries=6`
* [ ] jotto

# License
```
Copyright (C) Saeed Gholami Shahbandi
```
 
NOTE: Portions of this code/project were developed with the assistance of ChatGPT, a product of OpenAI.  
Distributed with a GNU GENERAL PUBLIC LICENSE; see [LICENSE](https://github.com/saeedghsh/quiz_games/blob/master/LICENSE).
