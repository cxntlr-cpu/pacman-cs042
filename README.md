# Pacman AI Lab

**Tell AI what you want Pacman to do. Watch the result. Try another idea.**

You can run this project on your computer or use GitHub Codespaces in your browser. No programming experience or paid AI API is required.

## 1. Install and start

Choose **one** guide and follow its numbered steps:

| Where will you work? | Start here |
| --- | --- |
| My Windows computer | [Install on Windows](instructions/install_on_windows.md) |
| My Mac | [Install on Mac](instructions/install_on_mac.md) |
| GitHub Codespaces, without installing locally | [Use Codespaces](instructions/use_in_codespaces.md) |

The local guides explain how to install Python, open the project, and start the game. Codespaces sets up Python for you. You can follow the steps yourself. If VS Code and Copilot are already open, the [installation prompt](prompts/01_install_and_start.prompt.md) can help with the remaining steps.

**What should open?** The start command opens a browser page with a program menu. Choose **Play yourself** and click **New game**. Use arrow keys or WASD. Keep the terminal open; press **Ctrl+C** to stop the game.

Individual programs can also use Berkeley’s desktop game window. If no desktop window can open, the launcher automatically switches to the browser and prints the address. Codespaces uses its forwarded browser link automatically.

## 2. Try a prompt

Open a file below. Copy the text inside its box into **Copilot Chat → Agent mode**, with this project folder open. Other coding assistants can use the same text. For the final two prompts, replace the bracketed line with **your own idea in everyday words**.

| What do you want to do? | Prompt |
| --- | --- |
| Install and open Pacman | [01 · Install and start](prompts/01_install_and_start.prompt.md) |
| Understand the project | [02 · Explain the project](prompts/02_explain_the_project.prompt.md) |
| See the choices and run one | [03 · Choose and run a program](prompts/03_choose_and_run_a_program.prompt.md) |
| Explore one route, then backtrack | [04 · Depth-first search](prompts/04_depth_first_search.prompt.md) |
| Find the fewest moves | [05 · Breadth-first search](prompts/05_breadth_first_search.prompt.md) |
| Find the cheapest route | [06 · Uniform-cost search](prompts/06_uniform_cost_search.prompt.md) |
| Search using an estimate | [07 · A* search](prompts/07_astar_search.prompt.md) |
| Create my own A* estimate | [08 · My A* heuristic](prompts/08_create_my_astar_heuristic.prompt.md) |
| Decide how Pacman behaves | [09 · My Pacman behavior](prompts/09_create_my_pacman_behavior.prompt.md) |

Each search prompt asks AI to **explain → build → check → run**. Play and Go west work immediately. The search algorithms are built in your own copy when you use their prompts.

## 3. Watch and experiment

In the browser, choose a program and click **Run experiment**. Pause, step, change speed, or drag the timeline. Colored squares show exploration; the green line shows the route. **Compare searches** puts their results together.

Try the **Cost maze**: orange squares cost 6 to enter; other steps cost 1. Compare **moves**, **travel cost**, and **search expansions**. Game score is a separate measure.

These names show you where things belong:

| File or folder | What it contains |
| --- | --- |
| `start_pacman.py` | The command that installs or starts Pacman. |
| `prompts/` | The short recipes you give to AI. |
| `my_astar_heuristic.py` | Your idea for estimating the cost left to the goal. |
| `my_pacman_behavior.py` | Your rule for choosing Pacman’s next move. |
| `instructions/` | Setup guides and instructor notes. |
| `pacman_app/` | The supporting game and browser code. |
| `berkeley_pacman/` | Berkeley’s project, downloaded once during installation. |
| `saved_replays/` | Replays you save later. |

After installation the game works offline. For a preview without installation, open [watch_pacman_go_west.html](examples/watch_pacman_go_west.html) in your browser.

**Need help?** Paste the error into your AI chat and say: “Fix the smallest cause, check it, and run again.” If port 8000 is busy, add `--port 8001` to the start command.

[More commands and notes for instructors](instructions/notes_for_instructors.md) · [Berkeley credits](CREDITS.md)
