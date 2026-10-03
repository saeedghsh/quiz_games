.PHONY: sync test test-browser build-pages serve-pages

sync:
	uv sync --locked

test:
	uv run --locked pytest -m "not browser"

test-browser:
	uv run --locked --group browser playwright install chromium
	RUN_BROWSER_TESTS=1 uv run --locked --group browser pytest -m browser

build-pages:
	uv run --locked python scripts/build_pages.py

serve-pages: build-pages
	uv run --locked python -m http.server 8000 --directory _site
