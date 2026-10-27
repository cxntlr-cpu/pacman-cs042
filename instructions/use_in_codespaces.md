# Use Pacman in GitHub Codespaces

Use this option to work in your browser. You do not need to install Python or VS Code on your computer. Codespaces availability and usage limits depend on your GitHub account.

## 1. Open the project

1. On this GitHub repo, select **Code → Codespaces → Create codespace**.
2. Wait for the editor and automatic Pacman installation to finish.
3. Open **Terminal → New Terminal**.
4. Run:

```sh
python3 start_pacman.py
```

If the automatic installation failed, run `python3 start_pacman.py install`, then try again.

## 2. Open the game

The launcher detects Codespaces and prints a forwarded browser link. Click it, or use **Ports → 8000 → Open in Browser** (the globe icon). Keep the port **Private**.

Choose **Play yourself → New game**. Use arrow keys or WASD. Leave the terminal running while playing. Press **Ctrl+C** to stop.

Use the Codespaces forwarded link, not your computer’s `localhost:8000`.

## 3. Talk to AI

Open Copilot Chat and select **Agent** mode. Open a file in the visible `prompts/` folder and paste the text inside its box into the chat. Start with [02 · Explain the project](../prompts/02_explain_the_project.prompt.md), then [03 · Choose and run](../prompts/03_choose_and_run_a_program.prompt.md).

AI can edit your files, run checks, and show the result through the same browser page. You can also describe a different experiment in your own words. Copilot access depends on your account.

When finished, stop your codespace from GitHub’s Codespaces page so it does not keep running.

[Back to the README](../README.md)
