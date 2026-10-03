# Browser architecture

The static app follows the approach in
[Distribution Playground](https://github.com/saeedghsh/distribution_playground/):
ship the existing Python engine to the browser and call it through Pyodide.
There is no application server and no JavaScript copy of the game rules.

`scripts/build_pages.py` copies `web/` into `_site/`, packages the canonical
`countdown`, `scowl`, and `utilities` modules with the US SCOWL dictionary, and
exports the Pyodide/Python pins from `pyproject.toml`. The terminal installation
retains all three bundled dictionaries. Dictionary paths are relative to their
module, so both installed commands and the Pyodide filesystem work from any
current directory.

The browser loads Pyodide 0.28.3 (Python 3.13) from jsDelivr in a module worker.
It checks runtime versions, unpacks the archive, and creates `BrowserGame`.
The UI sends an allowlisted JSON action to Python; it never interpolates user
answers into executable Python. `BrowserGame` owns round state and delegates
draws, validation, scores, and solutions to the same engine used by the TUI.
Terminal-only threading and `select` imports are lazy, so browser imports do
not require those facilities. The game itself has no third-party dependencies.

JavaScript handles rendering and the thinking timer. The timer uses a wall-clock
deadline to catch up after a background tab is resumed. As in the TUI, the end
of thinking time still allows an answer declaration; invalid number expressions
can be corrected. New rounds and mode switches discard the previous round.
Settings changed during a round apply to the next round (thinking time can also
be changed during letter selection).

The numbers search runs after submission, in the worker, with a 3-second search
budget instead of the TUI's 30 seconds. Result normalization can add time after
the search deadline. The UI labels incomplete searches as “best found,” displays
at most two expressions, and remains responsive while Python computes. Requests
are serialized and game controls are disabled during requests to prevent stale
results from replacing a newer round. A fatal worker/load timeout offers a reload.

The first visit requires internet access for the Pyodide CDN (and optional web
fonts). Serve `_site` over HTTP, not `file://`. Relative asset URLs support a
GitHub Pages repository subpath. There is no service worker or offline guarantee.

## Validation and deployment

```bash
uv sync --locked
make test
make build-pages
make serve-pages
```

The opt-in browser test loads real Pyodide, plays both games, checks invalid
expressions, timer expiration, solver output, and mobile overflow, and serves the
site at a nested path. It needs network access and a Chrome/Chromium installation:

```bash
make test-browser
# Or use an already-installed Chrome:
RUN_BROWSER_TESTS=1 BROWSER_EXECUTABLE=/usr/bin/google-chrome \
  uv run --locked --group browser pytest -m browser
```

The GitHub Actions workflow tests and builds on pushes and pull requests. To
publish, set the repository's Pages source to **GitHub Actions**, then run
**Test and build Pages** manually with **Deploy the built site** checked.
Any static host can serve the contents of `_site/`.
