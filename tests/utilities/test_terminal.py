# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=unused-import

import sys
from unittest.mock import patch
import pytest
from utilities.terminal import move_cursor_up, clear_line_content, timer


def test_move_cursor_up():
    with patch.object(sys.stdout, "write") as mock_write:
        move_cursor_up(5)
        mock_write.assert_called_once_with("\033[5A")
        move_cursor_up(10)
        mock_write.assert_called_with("\033[10A")


def test_clear_line_content():
    with patch.object(sys.stdout, "write") as mock_write:
        clear_line_content()
        mock_write.assert_called_once_with("\033[K")


def test_timer():
    with (
        patch("builtins.print") as mock_print,
        patch("utilities.terminal.time.sleep", return_value=None) as mock_sleep,
        patch("utilities.terminal.move_cursor_up") as mock_up,
        patch("utilities.terminal.clear_line_content") as mock_clear,
    ):
        timer(3)
        assert mock_sleep.call_count == 3
        assert mock_up.call_count == 3
        mock_clear.assert_called_once()
        mock_print.assert_any_call("Times up!\n")
        mock_print.assert_any_call("-", "\t3 seconds left")
        mock_print.assert_any_call("\\", "\t2 seconds left")
        mock_print.assert_any_call("|", "\t1 seconds left")


if __name__ == "__main__":
    pytest.main()
