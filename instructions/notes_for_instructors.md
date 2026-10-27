# Notes for instructors

## Student workflow

Install using one of the three setup guides, open the game, then use the numbered files in `prompts/`. Keep instructions short. Students describe their ideas in words; AI helps translate them into Python.

The two customization files are `my_astar_heuristic.py` and `my_pacman_behavior.py`. Search implementations are created in `berkeley_pacman/search.py`. Berkeley’s original filenames and attribution notices are preserved.

## Commands

On Mac and Codespaces, use `python3`. On Windows, replace it with `py -3` (or `python`).

```sh
python3 start_pacman.py install
python3 start_pacman.py check-installation
python3 start_pacman.py
python3 start_pacman.py go-west
python3 start_pacman.py breadth-first-search --maze tiny
python3 start_pacman.py uniform-cost-search --maze cost-maze
python3 start_pacman.py astar-search --maze medium --heuristic my-heuristic
python3 start_pacman.py my-pacman
python3 start_pacman.py compare-searches --maze cost-maze
```

The program menu and comparison use the browser. Individual games automatically use a working desktop window or fall back to the browser. Add `--display browser` to always use the browser, `--display desktop` to request the desktop window, or `--display text` for a result summary. A desktop graphics failure automatically opens the browser alternative. In Codespaces and SSH sessions, the launcher uses the browser.

The browser shows search exploration, playback controls, and comparison results. The native window shows Berkeley’s game. Travel cost and game score are separate; Classic contains multiple food dots, while search mazes contain one.

If an AI environment cannot expose a live browser port, export a replay and ask the assistant to attach it:

```sh
python3 start_pacman.py breadth-first-search --save-replay saved_replays/breadth_first_search.html
```

## Checks and publishing

Run `python3 -m unittest discover -s tests -v`. Unbuilt algorithms are skipped. CI is configured for Linux, Windows, and macOS; native graphics still need a visual check on each platform.

Keep the downloaded `berkeley_pacman/` folder and generated `saved_replays/` out of Git and manual uploads. Berkeley asks that completed assignment solutions not be published. See [credits and terms](../CREDITS.md).

Upload the project’s files to an empty GitHub repo, including the configuration folders. The student recipes belong in the visible `prompts/` folder; `.github/` contains GitHub configuration only. Enable **Template repository** in GitHub settings if each student should create their own copy.

[Back to the README](../README.md)
