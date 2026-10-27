import hashlib
import io
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request
import zipfile

from pacman_app import download_berkeley_project as bootstrap
from pacman_app.game_runner import (board_data, checked_heuristic, cost_function, heuristic_report,
                        load_engine, new_state, readiness, simulate, snapshot)
from pacman_app.browser_server import ManualGame, make_server, run_worker
from pacman_app.save_replay import save_replay


class SetupTests(unittest.TestCase):
    def archive(self, unsafe=False):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w") as archive:
            for name in bootstrap.REQUIRED:
                archive.writestr("search/" + name, "starter placeholder")
            if unsafe:
                archive.writestr("search/../../escape.py", "unsafe")
        return stream.getvalue()

    def test_checksum_is_required(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "engine"
            with self.assertRaisesRegex(ValueError, "checksum"):
                bootstrap.install_archive(b"wrong bytes", target)
            self.assertFalse(target.exists())

    def test_install_never_overwrites_work(self):
        data = self.archive()
        with tempfile.TemporaryDirectory() as directory, patch.object(bootstrap, "SHA256", hashlib.sha256(data).hexdigest()):
            target = Path(directory) / "engine"
            bootstrap.install_archive(data, target)
            (target / "search.py").write_text("my changes", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "never overwrites"):
                bootstrap.install_archive(data, target)
            self.assertEqual((target / "search.py").read_text(), "my changes")

    def test_unsafe_archive_paths_are_rejected(self):
        data = self.archive(unsafe=True)
        with tempfile.TemporaryDirectory() as directory, patch.object(bootstrap, "SHA256", hashlib.sha256(data).hexdigest()):
            with self.assertRaisesRegex(ValueError, "unexpected path"):
                bootstrap.install_archive(data, Path(directory) / "engine")
            self.assertFalse((Path(directory) / "escape.py").exists())


class EngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bootstrap.ensure_engine()
        cls.engine = load_engine()

    def test_default_demo_uses_berkeley_rules_and_wins(self):
        result = simulate("west", "west")
        self.assertTrue(result["won"])
        state = new_state(self.engine, "west")
        for action in result["actions"]:
            state = state.generateSuccessor(0, action)
        self.assertEqual(snapshot(state), result["frames"][-1])

    def test_west_stops_cleanly_at_a_wall(self):
        result = simulate("west", "tiny")
        self.assertEqual(result["status"], "Stopped at a wall")
        self.assertFalse(result["won"])

    def test_custom_agent_obeys_step_limit(self):
        result = simulate("custom", "classic", max_steps=4)
        self.assertLessEqual(result["moves"], 4)
        self.assertEqual(len(result["frames"]), result["moves"] + 1)

    def test_custom_illegal_move_is_actionable(self):
        with patch("my_pacman_behavior.choose_move", return_value="Teleport"):
            with self.assertRaisesRegex(ValueError, "legal_moves"):
                simulate("custom", "classic")

    def test_missing_search_has_matching_prompt(self):
        with patch("pacman_app.game_runner.readiness", return_value={"bfs": False}):
            with self.assertRaisesRegex(ValueError, "05_breadth_first_search.prompt.md"):
                simulate("bfs", "tiny")

    def test_search_rejects_classic_multi_food_maze(self):
        with self.assertRaisesRegex(ValueError, "single-food"):
            simulate("bfs", "classic")

    def test_custom_estimate_rejects_bad_values(self):
        for value in (float("nan"), float("inf"), -1, True, "one"):
            with self.subTest(value=value), patch("my_astar_heuristic.estimate", return_value=value):
                with self.assertRaisesRegex(ValueError, "finite"):
                    checked_heuristic("custom", (2, 2), (1, 1))

    def test_heuristic_consistency_and_goal_are_checked(self):
        state = new_state(self.engine, "tiny")
        self.assertIn("passes", heuristic_report("manhattan", state, lambda _: 1))
        with patch("my_astar_heuristic.estimate", return_value=1):
            with self.assertRaisesRegex(ValueError, "0 at the goal"):
                heuristic_report("custom", state, lambda _: 1)
        with patch("my_astar_heuristic.estimate", side_effect=lambda p, g: 2 * (abs(p[0]-g[0]) + abs(p[1]-g[1]))):
            self.assertIn("fails", heuristic_report("custom", state, lambda _: 1))

    def test_cost_maze_has_one_goal_and_expensive_squares(self):
        state = new_state(self.engine, "costly")
        self.assertEqual(state.getFood().asList(), [(1, 1)])
        board = board_data(state, "costly")
        self.assertTrue(board["mud"])
        cost = cost_function(board["mud"])
        self.assertEqual(cost(tuple(board["mud"][0])), 6)
        self.assertEqual(cost(state.getPacmanPosition()), 1)

    def test_worker_is_a_real_subprocess_replay(self):
        result = run_worker("west", "west")
        self.assertTrue(result["won"])
        self.assertEqual(result["frames"][-1]["score"], result["score"])

    def test_worker_timeout_is_actionable(self):
        import subprocess
        with patch("pacman_app.browser_server.subprocess.run", side_effect=subprocess.TimeoutExpired("demo", 20)):
            with self.assertRaisesRegex(ValueError, "20 seconds"):
                run_worker("west", "west")

    def test_export_embeds_the_real_replay_without_network_assets(self):
        result = simulate("west", "west")
        with tempfile.TemporaryDirectory() as directory:
            path = save_replay(result, Path(directory) / "demo.html")
            html = path.read_text(encoding="utf-8")
            self.assertIn('id="replay-data"', html)
            self.assertNotIn('src="/game_viewer.js"', html)
            self.assertNotIn('href="/game_viewer.css"', html)
            self.assertIn('"won": true', html)

    def test_export_data_cannot_break_out_of_its_script_block(self):
        result = simulate("west", "west")
        result["note"] = "</script><script>unexpected</script>"
        with tempfile.TemporaryDirectory() as directory:
            html = save_replay(result, Path(directory) / "demo.html").read_text(encoding="utf-8")
            self.assertNotIn("</script><script>unexpected", html)
            self.assertIn("\\u003c/script>", html)

    def test_manual_game_preserves_berkeley_transition(self):
        game = ManualGame("west", 7, 10)
        expected = game.state.generateSuccessor(0, "West")
        result = game.move("West")
        self.assertEqual(result["position"], list(expected.getPacmanPosition()))
        self.assertEqual(result["score"], expected.getScore())
        self.assertEqual(result["moves"], 1)

    def test_manual_ghosts_are_reproducible(self):
        first, second = ManualGame("classic", 7, 30), ManualGame("classic", 7, 30)
        for _ in range(10):
            legal = first.state.getLegalActions(0)
            action = next((direction for direction in ("West", "South", "East", "North") if direction in legal), "Stop")
            self.assertEqual(first.move(action), second.move(action))
            if first.payload()["finished"]:
                break


class BrowserApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bootstrap.ensure_engine()
        cls.server = make_server("127.0.0.1", 0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = "http://127.0.0.1:" + str(cls.server.server_port)
        cls.token = json.loads(urllib.request.urlopen(cls.base + "/api/config").read())["token"]

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def post(self, path, body, token=None):
        request = urllib.request.Request(self.base + path, data=json.dumps(body).encode(),
                                         headers={"Content-Type": "application/json", "X-Lab-Token": token or self.token})
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read())

    def test_assets_are_served_without_external_dependencies(self):
        for path in ("/", "/game_viewer.css", "/game_viewer.js"):
            with self.subTest(path=path), urllib.request.urlopen(self.base + path) as response:
                self.assertEqual(response.status, 200)
                self.assertIn("default-src 'self'", response.headers["Content-Security-Policy"])

    def test_requests_require_session_token(self):
        with self.assertRaises(urllib.error.HTTPError) as context:
            self.post("/api/start", {"maze": "tiny"}, token="wrong")
        self.assertEqual(context.exception.code, 403)

    def test_browser_game_and_replay(self):
        start = self.post("/api/start", {"maze": "west"})
        after = self.post("/api/move", {"session": start["session"], "action": "West"})
        self.assertEqual(after["moves"], 1)
        result = self.post("/api/run", {"mode": "west", "maze": "west", "heuristic": "manhattan"})
        self.assertTrue(result["won"])

    def test_browser_errors_are_clear(self):
        with self.assertRaises(urllib.error.HTTPError) as context:
            self.post("/api/start", {"maze": "../private"})
        self.assertEqual(context.exception.code, 400)
        payload = json.loads(context.exception.read())
        self.assertIn("maze", payload["error"])

    def test_static_paths_cannot_read_repository_files(self):
        with self.assertRaises(urllib.error.HTTPError) as context:
            urllib.request.urlopen(self.base + "/my_pacman_behavior.py")
        self.assertEqual(context.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
