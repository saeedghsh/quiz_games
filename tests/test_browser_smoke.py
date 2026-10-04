"""Opt-in integration test: real Pyodide, bundled Python, and browser controls."""

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
from threading import Thread

import pytest

from scripts.build_pages import build_pages

pytestmark = [
    pytest.mark.browser,
    pytest.mark.skipif(os.environ.get("RUN_BROWSER_TESTS") != "1", reason="Set RUN_BROWSER_TESTS=1 to load Pyodide in a browser"),
]


def test_real_pyodide_both_games_and_mobile(tmp_path):
    from playwright.sync_api import sync_playwright, expect

    # Serve at a nested path to catch broken GitHub Pages asset URLs.
    output = tmp_path / "quiz_games" / "_site"
    build_pages(output)
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=str(tmp_path)))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path=os.environ.get("BROWSER_EXECUTABLE"))
            page = browser.new_page(viewport={"width": 1360, "height": 1000})
            page.clock.install()
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(f"http://127.0.0.1:{server.server_port}/quiz_games/_site/")
            expect(page.locator("#app")).to_be_visible(timeout=120000)
            page.locator("#new-round").click()
            page.locator("#vowel").click()
            expect(page.locator(".tile:not(.blank)")).to_have_count(1)
            page.locator("#fill").click()
            expect(page.locator(".tile:not(.blank)")).to_have_count(9)
            # Advance wall time to exercise the thinking timer without sleeping.
            page.clock.fast_forward(31000)
            expect(page.locator("#time")).to_have_text("0")
            expect(page.locator("#answer")).to_be_visible()
            page.locator("#answer").fill("zzzzzzzzzzzzzz")
            page.locator("#submit").click()
            expect(page.locator("#score")).to_have_text("0 points")
            expect(page.locator("#solution-status")).not_to_have_text("Finding the best possibilities…", timeout=15000)
            page.locator("#numbers-mode").click()
            expect(page.locator(".tile")).to_have_count(6)
            page.locator("#answer").fill("1 ** 2")
            page.locator("#submit").click()
            expect(page.locator("#feedback")).to_be_visible()
            first = page.locator(".tile").first.inner_text()
            page.locator("#answer").fill(first)
            page.locator("#submit").click()
            expect(page.locator("#results")).to_be_visible()
            expect(page.locator("#solutions code").first).to_be_visible(timeout=60000)
            page.screenshot(path=str(tmp_path / "numbers-desktop.png"), full_page=True)
            page.set_viewport_size({"width": 390, "height": 844})
            page.locator("#words-mode").click()
            page.locator("#fill").click()
            page.screenshot(path=str(tmp_path / "words-mobile.png"), full_page=True)
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")

            page.locator("#letter-count").select_option("6")
            page.locator("#word-language").select_option("fa")
            expect(page.locator("#letter-count")).to_have_value("9")
            expect(page.locator(".tile")).to_have_count(9)
            expect(page.locator(".board")).to_have_attribute("dir", "rtl")
            expect(page.locator(".board")).to_have_attribute("lang", "fa")
            expect(page.locator("#vowel")).to_have_text("+ مصوت")
            expect(page.locator("#consonant")).to_have_text("+ صامت")
            expect(page.locator(".tile:not(.blank)")).to_have_count(0)
            page.locator("#vowel").click()
            expect(page.locator(".tile:not(.blank)")).to_have_count(1)
            from countdown.farsi import FARSI_ALPHABET, FARSI_VOWELS

            assert page.locator(".tile").nth(0).inner_text() in FARSI_VOWELS
            page.locator("#consonant").click()
            expect(page.locator(".tile:not(.blank)")).to_have_count(2)
            assert page.locator(".tile").nth(1).inner_text() in set(FARSI_ALPHABET) - set(FARSI_VOWELS)
            page.screenshot(path=str(tmp_path / "farsi-draw-mobile.png"), full_page=True)
            page.locator("#fill").click()
            expect(page.locator("#answer")).to_have_attribute("dir", "rtl")
            # Compare this random round with native Python; even a draw with no
            # solutions has a deterministic expected score and solver result.
            from countdown.farsi import farsi_corpus
            from countdown.letter_countdown import LetterCountdown

            game = LetterCountdown(farsi_corpus())
            game.letters = page.locator(".tile").all_text_contents()
            best = game.optimal_solutions()
            answer = best[0] if best else "نامعتبرنامعتبر"
            keyboard_answer = answer.replace("ک", "ك").replace("ی", "ي")
            page.locator("#answer").fill(keyboard_answer)
            page.locator("#submit").click()
            expect(page.locator("#score")).to_have_text(f"{game.score_response(answer)} امتیاز")
            expect(page.locator("#solution-status")).not_to_have_text("در حال یافتن بهترین واژه‌ها…", timeout=20000)
            expect(page.locator("#solutions")).to_have_text(" · ".join(best))
            expect(page.locator("#word-language")).to_be_enabled()
            page.screenshot(path=str(tmp_path / "farsi-mobile.png"), full_page=True)
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            page.set_viewport_size({"width": 1360, "height": 1000})
            page.screenshot(path=str(tmp_path / "farsi-desktop.png"), full_page=True)
            page.locator("#numbers-mode").click()
            expect(page.locator(".board")).to_have_attribute("dir", "ltr")
            expect(page.locator("#language-setting")).to_be_hidden()
            page.locator("#words-mode").click()
            expect(page.locator(".board")).to_have_attribute("dir", "rtl")
            page.locator("#word-language").select_option("en")
            expect(page.locator("#letter-count")).to_have_value("6")
            expect(page.locator(".tile")).to_have_count(6)
            expect(page.locator(".board")).to_have_attribute("dir", "ltr")
            expect(page.locator("#vowel")).to_be_visible()
            expect(page.locator("#vowel")).to_have_text("+ Vowel")
            expect(page.locator("#consonant")).to_have_text("+ Consonant")
            expect(page.locator("#results")).to_be_hidden()
            expect(page.locator("#answer")).to_have_value("")
            assert not errors
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
