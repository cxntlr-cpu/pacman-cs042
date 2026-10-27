#!/usr/bin/env python3
"""Install, launch, and choose how to watch a Pacman experiment."""
import argparse
import json
import os
import sys

# Read student edits from source, including quick edits of the same file length.
sys.dont_write_bytecode = True
sys.pycache_prefix = os.path.join(os.path.dirname(os.path.abspath(__file__)), "berkeley_pacman", ".unused_bytecode")

from pacman_app.download_berkeley_project import ensure_engine

PROGRAMS = {
    "menu": "play", "play": "play", "go-west": "west",
    "depth-first-search": "dfs", "breadth-first-search": "bfs",
    "uniform-cost-search": "ucs", "astar-search": "astar",
    "my-pacman": "custom", "compare-searches": "compare",
}
MAZES = {"tiny": "tiny", "medium": "medium", "cost-maze": "costly",
         "classic": "classic", "go-west-demo": "west"}
HEURISTICS = {"manhattan-distance": "manhattan", "my-heuristic": "custom"}


def parser():
    p = argparse.ArgumentParser(description="Pacman AI Lab: install, play, and explore search.")
    p.add_argument("program", nargs="?", default="menu",
                   choices=[*PROGRAMS, "install", "check-installation", "_record-game"],
                   metavar="program", help="Choose a program; the default opens the browser menu.")
    p.add_argument("--maze", choices=MAZES)
    p.add_argument("--heuristic", choices=HEURISTICS, default="manhattan-distance")
    p.add_argument("--display", choices=["auto", "browser", "desktop", "text"], default="auto",
                   help="Automatically choose a working display, or request one.")
    p.add_argument("--save-replay", metavar="FILE.html", help="Save a replay that opens offline in a browser.")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--no-open-browser", action="store_true", help="Print the link without opening a browser tab.")
    p.add_argument("--random-seed", type=int, default=7)
    p.add_argument("--max-moves", type=int, default=250)
    p.add_argument("--host", choices=["127.0.0.1", "0.0.0.0"], default="127.0.0.1", help=argparse.SUPPRESS)
    p.add_argument("--mode", default="west", help=argparse.SUPPRESS)
    return p


def choose_display(program, preference):
    """Menus need the browser; individual games can also use Berkeley's window."""
    if preference == "text":
        return "text"
    if program in ("menu", "compare-searches"):
        if preference == "desktop":
            print("The program menu and search comparison open in your browser.")
        return "browser"
    if preference == "browser":
        return "browser"
    from pacman_app.game_runner import desktop_window_available
    if desktop_window_available():
        return "desktop"
    print("A desktop game window is unavailable here. Using the browser game instead.", flush=True)
    return "browser"


def open_browser_game(args, mode, maze, heuristic):
    from pacman_app.browser_server import serve
    serve(mode, maze, heuristic, args.host, args.port, not args.no_open_browser,
          args.random_seed, args.max_moves)


def main(argv=None):
    p = parser()
    args = p.parse_args(argv)
    if sys.version_info < (3, 10):
        p.error("Install Python 3.12 or newer from https://www.python.org/downloads/.")
    if not 1 <= args.max_moves <= 1000 or not 1 <= args.port <= 65535:
        p.error("Use 1–1000 moves and a port between 1 and 65535.")
    try:
        ensure_engine(quiet=args.program == "_record-game")
        from pacman_app.game_runner import default_maze, readiness, simulate
        heuristic = HEURISTICS[args.heuristic]
        if args.program == "install":
            command = "py -3" if os.name == "nt" else "python3"
            print(f"Installation complete. Start Pacman with: {command} start_pacman.py")
            return 0
        if args.program == "check-installation":
            result = simulate("west", "west")
            if not result["won"]:
                raise ValueError("The Berkeley game check did not finish successfully.")
            print("Installation works. The game and browser viewer are ready.")
            for mode, ready in readiness().items():
                name = next(name for name, value in PROGRAMS.items() if value == mode)
                print(f"{name}: {'ready' if ready else 'use its prompt in prompts/ to build it'}")
            return 0
        mode = args.mode if args.program == "_record-game" else PROGRAMS[args.program]
        maze = MAZES[args.maze] if args.maze else default_maze(mode)
        if args.program == "_record-game":
            print(json.dumps(simulate(mode, maze, heuristic, args.random_seed, args.max_moves), allow_nan=False))
            return 0
        if args.save_replay:
            if args.program in ("play", "menu"):
                p.error("Choose a recorded experiment, for example: start_pacman.py go-west --save-replay saved_replays/demo.html")
            from pacman_app.browser_server import run_comparison, run_worker
            from pacman_app.save_replay import save_replay
            result = (run_comparison(maze, heuristic, args.random_seed, args.max_moves) if mode == "compare"
                      else run_worker(mode, maze, heuristic, args.random_seed, args.max_moves))
            print("Open this replay in your browser: " + str(save_replay(result, args.save_replay)))
            return 0
        display = choose_display(args.program, args.display)
        if display == "browser":
            open_browser_game(args, mode, maze, heuristic)
        elif display == "desktop":
            from pacman_app.game_runner import DesktopWindowUnavailable, run_desktop_game
            try:
                run_desktop_game(mode, maze, heuristic, args.random_seed, args.max_moves)
            except DesktopWindowUnavailable:
                print("The desktop window could not open. Using the browser game instead.", flush=True)
                open_browser_game(args, mode, maze, heuristic)
        else:
            if args.program in ("menu", "play", "compare-searches"):
                p.error("This program needs a visual display. Remove --display text.")
            from pacman_app.browser_server import run_worker
            result = run_worker(mode, maze, heuristic, args.random_seed, args.max_moves)
            print(json.dumps({key: result[key] for key in (
                "mode", "maze", "status", "moves", "cost", "expanded", "score")}, indent=2))
        return 0
    except KeyboardInterrupt:
        print("\nPacman closed.")
        return 0
    except Exception as exc:
        if args.program == "_record-game":
            print(json.dumps({"error": str(exc)}))
        else:
            print(f"Could not start: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
