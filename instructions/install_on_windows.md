# Install and run on Windows

## 1. Install the tools

- Install Python from [python.org](https://www.python.org/downloads/windows/). Use Python 3.12 or newer. If the installer offers **Add Python to PATH**, select it.
- Install [Visual Studio Code](https://code.visualstudio.com/).

Already installed? Keep what you have if Python is version 3.10 or newer.

## 2. Open this project

1. On this GitHub repo, select **Code → Download ZIP**.
2. Right-click the ZIP and select **Extract All**. Work in the extracted folder.
3. Open VS Code. Select **File → Open Folder** and choose the folder containing `README.md` and `start_pacman.py`.
4. Select **Terminal → New Terminal**. You will type the commands below there.

## 3. Install Pacman and start it

Copy and run each line, waiting for it to finish before running the next:

```powershell
py -3 start_pacman.py install
py -3 start_pacman.py
```

The first command downloads Berkeley’s starter once. The second starts the game and opens your browser at **http://localhost:8000**. If the tab does not open, enter that address yourself.

Choose **Play yourself → New game**. Use arrow keys or WASD. Keep the terminal running. Press **Ctrl+C** when finished.

**If `py` is not recognized:** replace `py -3` with `python` in both commands. If neither works, finish installing Python, close and reopen VS Code, and try again. Check the version with `py -3 --version` or `python --version`.

## 4. Try AI help

Open Copilot Chat in VS Code, sign in if requested, and choose **Agent** mode so it can edit files and run commands. Your Copilot access depends on your account.

Open [02_explain_the_project.prompt.md](../prompts/02_explain_the_project.prompt.md), copy the text in its box, and paste it into the chat. Then try [03_choose_and_run_a_program.prompt.md](../prompts/03_choose_and_run_a_program.prompt.md).

Use [01_install_and_start.prompt.md](../prompts/01_install_and_start.prompt.md) if setup needs help. Ordinary chat assistants can explain the steps but cannot run them on your computer.

[Back to the README](../README.md)
