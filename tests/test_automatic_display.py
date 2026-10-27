import contextlib
import io
import os
import subprocess
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import start_pacman
from pacman_app.game_runner import DesktopWindowUnavailable, desktop_window_available
from pacman_app.browser_server import serve


class AutomaticDisplayTests(unittest.TestCase):
    def test_headless_game_automatically_uses_browser(self):
        with patch("pacman_app.game_runner.desktop_window_available", return_value=False), contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(start_pacman.choose_display("go-west", "auto"), "browser")
        self.assertIn("browser", output.getvalue())

    def test_requested_desktop_also_falls_back_when_missing(self):
        with patch("pacman_app.game_runner.desktop_window_available", return_value=False), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(start_pacman.choose_display("play", "desktop"), "browser")

    def test_available_native_window_is_used_for_named_program(self):
        with patch("pacman_app.game_runner.desktop_window_available", return_value=True):
            self.assertEqual(start_pacman.choose_display("go-west", "auto"), "desktop")

    def test_program_menu_and_comparison_do_not_require_tk(self):
        with patch("pacman_app.game_runner.desktop_window_available", side_effect=AssertionError("Tk should not be checked")):
            for program in ("menu", "compare-searches"):
                self.assertEqual(start_pacman.choose_display(program, "auto"), "browser")

    def test_explicit_browser_does_not_probe_desktop(self):
        with patch("pacman_app.game_runner.desktop_window_available", side_effect=AssertionError("Tk should not be checked")):
            self.assertEqual(start_pacman.choose_display("go-west", "browser"), "browser")

    def test_codespaces_skips_native_window_probe(self):
        with patch.dict(os.environ, {"CODESPACES": "true"}, clear=True), patch("pacman_app.game_runner.subprocess.run") as probe:
            self.assertFalse(desktop_window_available())
            probe.assert_not_called()

    def test_failed_tk_probe_recovers(self):
        with patch.dict(os.environ, {}, clear=True), patch("pacman_app.game_runner.subprocess.run", return_value=SimpleNamespace(returncode=1)):
            self.assertFalse(desktop_window_available())

    def test_slow_tk_probe_cannot_block_launch(self):
        with patch.dict(os.environ, {}, clear=True), patch("pacman_app.game_runner.subprocess.run", side_effect=subprocess.TimeoutExpired("tk", 5)):
            self.assertFalse(desktop_window_available())

    def test_desktop_open_failure_still_launches_same_game_in_browser(self):
        with patch("start_pacman.ensure_engine"), patch("start_pacman.choose_display", return_value="desktop"), patch(
            "pacman_app.game_runner.run_desktop_game", side_effect=DesktopWindowUnavailable("cannot open")
        ), patch("start_pacman.open_browser_game") as browser, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(start_pacman.main(["go-west"]), 0)
            self.assertEqual(browser.call_args.args[1:], ("west", "west", "manhattan"))

    def test_code_errors_are_not_mistaken_for_missing_graphics(self):
        with patch("start_pacman.ensure_engine"), patch("start_pacman.choose_display", return_value="desktop"), patch(
            "pacman_app.game_runner.run_desktop_game", side_effect=ValueError("invalid behavior rule")
        ), patch("start_pacman.open_browser_game") as browser, contextlib.redirect_stderr(io.StringIO()) as output:
            self.assertEqual(start_pacman.main(["my-pacman"]), 1)
            browser.assert_not_called()
            self.assertIn("invalid behavior rule", output.getvalue())

    def test_codespaces_prints_forwarded_address_and_port_instructions(self):
        environment = {"CODESPACES": "true", "CODESPACE_NAME": "classroom-demo",
                       "GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN": "app.github.dev"}
        with patch.dict(os.environ, environment, clear=True), patch("pacman_app.browser_server.make_server") as server_factory, contextlib.redirect_stdout(io.StringIO()) as output:
            serve("play", "classic", "manhattan", "127.0.0.1", 8000, False)
            self.assertEqual(server_factory.call_args.args[0], "0.0.0.0")
            server_factory.return_value.serve_forever.assert_called_once()
            text = output.getvalue()
            self.assertIn("https://classroom-demo-8000.app.github.dev/", text)
            self.assertIn("Ports", text)
            self.assertIn("Private", text)
            self.assertNotIn("localhost", text)


if __name__ == "__main__":
    unittest.main()
