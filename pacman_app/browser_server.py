"""Local browser view. Standard library only; no hosted service or API key."""
from collections import OrderedDict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import random
import secrets
import subprocess
import sys
import threading
from urllib.parse import urlsplit
import webbrowser

from pacman_app.download_berkeley_project import ROOT
from pacman_app.game_runner import (SEARCH, board_data, load_engine,
                        new_state, readiness, snapshot, validate)

WEB = Path(__file__).parent / "browser"


def run_worker(mode, maze, heuristic="manhattan", seed=7, steps=250):
    validate(mode, maze, heuristic)
    try:
        completed = subprocess.run(
            [sys.executable, str(ROOT / "start_pacman.py"), "_record-game", "--mode", mode,
             "--maze", {"costly": "cost-maze", "west": "go-west-demo"}.get(maze, maze),
             "--heuristic", "my-heuristic" if heuristic == "custom" else "manhattan-distance",
             "--random-seed", str(seed), "--max-moves", str(steps)],
            cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=20,
        )
    except subprocess.TimeoutExpired as exc:
        raise ValueError("This run took over 20 seconds. Ask your AI to check for loops, then try again.") from exc
    try:
        result = json.loads(completed.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError) as exc:
        raise ValueError("The program could not run. Run the same command with --display text to inspect the error.") from exc
    if "error" in result:
        raise ValueError(result["error"])
    if completed.returncode:
        raise ValueError("The game process exited unexpectedly. Ask your AI to check the terminal.")
    return result


def run_comparison(maze, heuristic="manhattan", seed=7, steps=250):
    rows = []
    for algorithm in SEARCH:
        try:
            rows.append(run_worker(algorithm, maze, heuristic, seed, steps))
        except ValueError as exc:
            rows.append({"mode": algorithm, "error": str(exc)})
    return {"comparison": rows}


class ManualGame:
    def __init__(self, maze, seed, steps):
        validate("play", maze, "manhattan")
        self.engine = load_engine()
        self.state = new_state(self.engine, maze)
        self.board = board_data(self.state, maze)
        self.ghosts = [self.engine.ghostAgents.RandomGhost(i) for i in range(1, self.state.getNumAgents())]
        self.rng = random.Random(seed)
        self.moves, self.limit = 0, steps

    def payload(self):
        s = snapshot(self.state)
        status = "Food collected!" if s["won"] else "Caught by a ghost" if s["lost"] else "Step limit reached" if self.moves >= self.limit else "Your turn · arrow keys or WASD"
        return {**self.board, **s, "moves": self.moves, "status": status,
                "finished": s["won"] or s["lost"] or self.moves >= self.limit}

    def move(self, action):
        if action not in ("North", "South", "East", "West", "Stop"):
            raise ValueError("Use the arrow keys or direction buttons.")
        if self.payload()["finished"] or action not in self.state.getLegalActions(0):
            return self.payload()
        self.state = self.state.generateSuccessor(0, action)
        # Berkeley's ghosts use Python's global RNG; preserve an independent stream per game.
        previous = random.getstate()
        random.setstate(self.rng.getstate())
        try:
            for ghost in self.ghosts:
                if self.state.isWin() or self.state.isLose():
                    break
                self.state = self.state.generateSuccessor(ghost.index, ghost.getAction(self.state))
            self.rng.setstate(random.getstate())
        finally:
            random.setstate(previous)
        self.moves += 1
        return self.payload()


def make_server(host, port, mode="play", maze="classic", heuristic="manhattan", seed=7, steps=250):
    token = secrets.token_urlsafe(24)
    games, lock = OrderedDict(), threading.Lock()
    workers = threading.BoundedSemaphore(2)
    initial = {"mode": mode, "maze": maze, "heuristic": heuristic}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def reply(self, data, status=200, content_type="application/json; charset=utf-8"):
            raw = data if isinstance(data, bytes) else json.dumps(data, allow_nan=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; base-uri 'none'; form-action 'none'")
            self.end_headers()
            try:
                self.wfile.write(raw)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def do_GET(self):
            path = urlsplit(self.path).path
            if path == "/api/config":
                self.reply({"token": token, "initial": initial, "ready": readiness()})
                return
            assets = {"/": ("game_viewer.html", "text/html; charset=utf-8"),
                      "/game_viewer.js": ("game_viewer.js", "text/javascript; charset=utf-8"),
                      "/game_viewer.css": ("game_viewer.css", "text/css; charset=utf-8")}
            if path not in assets:
                self.reply({"error": "Not found"}, 404)
                return
            name, mime = assets[path]
            self.reply((WEB / name).read_bytes(), content_type=mime)

        def do_POST(self):
            if self.headers.get("X-Lab-Token") != token:
                self.reply({"error": "Reload this page to reconnect."}, 403)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 4096:
                    raise ValueError("Invalid request size.")
                body = json.loads(self.rfile.read(length))
                if not isinstance(body, dict):
                    raise ValueError("Invalid request.")
                path = urlsplit(self.path).path
                if path == "/api/run":
                    run_mode, run_maze, run_heuristic = (body.get(k) for k in ("mode", "maze", "heuristic"))
                    if not all(isinstance(x, str) for x in (run_mode, run_maze, run_heuristic)):
                        raise ValueError("Choose a program, maze, and heuristic.")
                    if not workers.acquire(blocking=False):
                        self.reply({"error": "Another run is finishing. Try again in a moment."}, 429)
                        return
                    try:
                        if run_mode == "compare":
                            result = run_comparison(run_maze, run_heuristic, seed, steps)
                        else:
                            result = run_worker(run_mode, run_maze, run_heuristic, seed, steps)
                    finally:
                        workers.release()
                    self.reply(result)
                elif path == "/api/start":
                    with lock:
                        maze_name = body.get("maze", "classic")
                        if not isinstance(maze_name, str):
                            raise ValueError("Choose a maze.")
                        session = secrets.token_urlsafe(16)
                        game = ManualGame(maze_name, seed, steps)
                        if len(games) >= 20:
                            games.popitem(last=False)
                        games[session] = game
                        self.reply({**game.payload(), "session": session})
                elif path == "/api/move":
                    with lock:
                        session = body.get("session")
                        if not isinstance(session, str) or session not in games:
                            raise ValueError("Click Run to start a new game.")
                        self.reply(games[session].move(body.get("action")))
                else:
                    self.reply({"error": "Not found"}, 404)
            except (ValueError, TypeError, KeyError) as exc:
                self.reply({"error": str(exc)}, 400)
            except Exception as exc:
                self.reply({"error": f"The game could not finish: {exc}"}, 500)

    server = ThreadingHTTPServer((host, port), Handler)
    server.daemon_threads = True
    return server


def serve(mode, maze, heuristic, host, port, open_browser, seed=7, steps=250):
    if os.environ.get("CODESPACES") == "true" or os.environ.get("CODESPACE_NAME"):
        host = "0.0.0.0"
    try:
        server = make_server(host, port, mode, maze, heuristic, seed, steps)
    except OSError as exc:
        raise ValueError(f"Port {port} is unavailable. Try --port {port + 1}.") from exc
    name = os.environ.get("CODESPACE_NAME")
    domain = os.environ.get("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN", "app.github.dev")
    url = f"https://{name}-{port}.{domain}/" if name else f"http://localhost:{port}/"
    print(f"\nOpen Pacman in your browser: {url}", flush=True)
    if name:
        print(f"In Codespaces: Ports → {port} → Open in Browser (globe icon). Keep the port Private.", flush=True)
    print("Keep this terminal running. Stop with Ctrl+C.", flush=True)
    if open_browser and not name:
        def open_tab():
            try:
                opened = webbrowser.open(url)
            except webbrowser.Error:
                opened = False
            if not opened:
                print(f"Open this address on the computer running Pacman: {url}", flush=True)
        threading.Timer(0.5, open_tab).start()
    try:
        server.serve_forever()
    finally:
        server.server_close()
