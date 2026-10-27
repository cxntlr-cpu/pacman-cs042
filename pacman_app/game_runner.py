"""Small adapters; game rules and state transitions come from Berkeley."""
import ast
import importlib
import math
import os
import random
import subprocess
import sys
import time
from types import SimpleNamespace

from pacman_app.download_berkeley_project import ENGINE, ROOT

SEARCH = {"dfs": "depthFirstSearch", "bfs": "breadthFirstSearch",
          "ucs": "uniformCostSearch", "astar": "aStarSearch"}
MAZES = {"tiny": "tinyMaze", "medium": "mediumMaze", "classic": "smallClassic", "west": "testMaze"}
MODES = ("play", "west", "dfs", "bfs", "ucs", "astar", "custom", "compare")


def default_maze(mode):
    return "classic" if mode in ("play", "custom") else "west" if mode == "west" else "costly" if mode == "compare" else "tiny"


def load_engine():
    if str(ENGINE) not in sys.path:
        sys.path.insert(0, str(ENGINE))
    names = ("pacman", "game", "layout", "search", "searchAgents", "ghostAgents")
    return SimpleNamespace(**{name: importlib.import_module(name) for name in names})


def readiness():
    try:
        tree = ast.parse((ENGINE / "search.py").read_text(encoding="utf-8"))
        functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
        def implemented(name):
            node = functions.get(name)
            return node is not None and not any(
                isinstance(part, ast.Attribute) and part.attr == "raiseNotDefined"
                for part in ast.walk(node))
        return {mode: implemented(name) for mode, name in SEARCH.items()}
    except (OSError, SyntaxError):
        return {mode: False for mode in SEARCH}


def get_layout(engine, name):
    if name == "costly":
        path = ROOT / "pacman_app" / "mazes" / "maze_with_costly_squares.lay"
    elif name in MAZES:
        path = ENGINE / "layouts" / (MAZES[name] + ".lay")
    else:
        raise ValueError("Choose a maze from the menu.")
    return engine.layout.Layout(path.read_text(encoding="utf-8").splitlines())


def mud_cells(maze, walls):
    return [(x, 2) for x in range(3, 14) if not walls[x][2]] if maze == "costly" else []


def cost_function(mud):
    mud = set(mud)
    return lambda position: 6 if position in mud else 1


def new_state(engine, maze):
    board = get_layout(engine, maze)
    state = engine.pacman.GameState()
    state.initialize(board, board.getNumGhosts())
    return state


def snapshot(state):
    return {
        "position": list(state.getPacmanPosition()),
        "direction": state.getPacmanState().getDirection(),
        "food": state.getFood().asList(), "capsules": state.getCapsules(),
        "ghosts": [{"position": list(ghost.getPosition()), "scared": ghost.scaredTimer > 0}
                   for ghost in state.getGhostStates()],
        "score": state.getScore(), "won": state.isWin(), "lost": state.isLose(),
    }


def board_data(state, maze):
    walls = state.getWalls()
    return {"width": walls.width, "height": walls.height, "walls": walls.asList(),
            "mud": mud_cells(maze, walls)}


def context_for(state):
    return {**snapshot(state), "legal_moves": state.getLegalActions(0),
            "walls": state.getWalls().asList()}


def custom_agent(engine):
    module = importlib.import_module("my_pacman_behavior")
    class MyAgent(engine.game.Agent):
        def __init__(self):
            super().__init__(index=0)
            self.memory = {}

        def getAction(self, state):
            action = module.choose_move(context_for(state), self.memory)
            if action not in state.getLegalActions(0):
                raise ValueError(f"my_pacman_behavior.py returned {action!r}. Return one of context['legal_moves'].")
            return action
    return MyAgent()


def checked_heuristic(kind, position, goal):
    if kind == "manhattan":
        value = abs(position[0] - goal[0]) + abs(position[1] - goal[1])
    else:
        value = importlib.import_module("my_astar_heuristic").estimate(position, goal)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError("my_astar_heuristic.py must return a finite, non-negative number.")
    return value


def heuristic_report(kind, state, cost_fn):
    goal = (1, 1)
    if checked_heuristic(kind, goal, goal) != 0:
        raise ValueError("The heuristic must return 0 at the goal (1, 1).")
    walls = state.getWalls()
    estimates = {(x, y): checked_heuristic(kind, (x, y), goal)
                 for x in range(walls.width) for y in range(walls.height) if not walls[x][y]}
    for (x, y), value in estimates.items():
        for nxt in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if nxt in estimates and value > cost_fn(nxt) + estimates[nxt] + 1e-9:
                return "This heuristic fails a consistency check on this maze; a cheapest route is not guaranteed."
    return "Heuristic passes consistency checks on this maze (other mazes may differ)."


def plan_route(engine, mode, state, maze, heuristic):
    if not readiness()[mode]:
        prompt = {"dfs": "04_depth_first_search", "bfs": "05_breadth_first_search",
                  "ucs": "06_uniform_cost_search", "astar": "07_astar_search"}[mode]
        raise ValueError(f"{mode.upper()} is not built yet. Paste prompts/{prompt}.prompt.md into your AI chat first, then run again.")
    visits = []
    class TracedProblem(engine.searchAgents.PositionSearchProblem):
        def getSuccessors(self, state):
            visits.append(state)
            return super().getSuccessors(state)
    cost_fn = cost_function(mud_cells(maze, state.getWalls()))
    problem = TracedProblem(state, costFn=cost_fn, warn=False, visualize=False)
    note = heuristic_report(heuristic, state, cost_fn) if mode == "astar" else ""
    function = getattr(engine.search, SEARCH[mode])
    started = time.perf_counter()
    if mode == "astar":
        actions = function(problem, heuristic=lambda pos, prob: checked_heuristic(heuristic, pos, prob.goal))
    else:
        actions = function(problem)
    elapsed = (time.perf_counter() - started) * 1000
    if not isinstance(actions, (list, tuple)):
        raise ValueError("The search function must return a list of directions.")
    # Validate the whole plan without hiding an illegal move behind a partial replay.
    x, y = problem.getStartState()
    for action in actions:
        if action not in ("North", "South", "East", "West"):
            raise ValueError(f"The search returned an invalid direction: {action!r}.")
        dx, dy = engine.game.Actions.directionToVector(action)
        x, y = int(x + dx), int(y + dy)
        if not 0 <= x < problem.walls.width or not 0 <= y < problem.walls.height or problem.walls[x][y]:
            raise ValueError("The search returned a route through a wall. Ask your AI to fix it.")
    if (x, y) != problem.goal:
        raise ValueError("The search returned a route that does not reach the food. Ask your AI to fix it.")
    return list(actions), visits, problem.getCostOfActions(actions), elapsed, note


def validate(mode, maze, heuristic):
    if mode not in MODES or mode == "compare":
        raise ValueError("Choose a program from the menu.")
    if maze not in (*MAZES, "costly") or heuristic not in ("manhattan", "custom"):
        raise ValueError("Choose a maze and heuristic from the menu.")
    if mode in SEARCH and maze not in ("tiny", "medium", "costly"):
        raise ValueError("Search needs a single-food maze: choose Tiny, Medium, or Cost maze.")


def simulate(mode, maze, heuristic="manhattan", seed=7, max_steps=250):
    validate(mode, maze, heuristic)
    random.seed(seed)
    engine = load_engine()
    state = new_state(engine, maze)
    board = board_data(state, maze)
    frames, visits, actions, elapsed, note = [snapshot(state)], [], [], None, ""
    planned_cost = None
    if mode in SEARCH:
        actions, visits, planned_cost, elapsed, note = plan_route(engine, mode, state, maze, heuristic)
    elif mode == "play":
        raise ValueError("Use the browser or --display desktop to play with arrow keys.")
    else:
        agent = engine.searchAgents.GoWestAgent() if mode == "west" else custom_agent(engine)
    ghosts = [engine.ghostAgents.RandomGhost(i) for i in range(1, state.getNumAgents())]
    cost, stopped = 0, False
    step_cost = cost_function(board["mud"])
    for turn in range(max_steps):
        if state.isWin() or state.isLose():
            break
        if mode in SEARCH:
            if turn >= len(actions):
                break
            action = actions[turn]
        else:
            action = agent.getAction(state)
            actions.append(action)
        if action not in state.getLegalActions(0):
            raise ValueError(f"The agent chose an illegal move: {action!r}.")
        if action == "Stop" and mode == "west":
            stopped = True
            break
        state = state.generateSuccessor(0, action)
        cost += step_cost(state.getPacmanPosition())
        for ghost in ghosts:
            if state.isWin() or state.isLose():
                break
            state = state.generateSuccessor(ghost.index, ghost.getAction(state))
        frames.append(snapshot(state))
    status = "Food collected!" if state.isWin() else "Caught by a ghost" if state.isLose() else "Stopped at a wall" if stopped else "Step limit reached"
    return {**board, "mode": mode, "maze": maze, "heuristic": heuristic,
            "frames": frames, "visits": visits, "actions": actions[:len(frames) - 1],
            "moves": len(frames) - 1, "cost": cost, "planned_cost": planned_cost,
            "expanded": len(visits), "search_ms": elapsed, "note": note,
            "status": status, "won": state.isWin(), "score": state.getScore(), "seed": seed}


class DesktopWindowUnavailable(RuntimeError):
    """A graphics issue the launcher can recover from by opening the browser."""


def desktop_window_available():
    """Probe Tk separately so a broken graphics installation cannot crash the launcher."""
    if os.environ.get("CODESPACES") == "true" or os.environ.get("CODESPACE_NAME") or os.environ.get("SSH_CONNECTION"):
        return False
    try:
        result = subprocess.run(
            [sys.executable, "-c", "import tkinter; window=tkinter.Tk(); window.withdraw(); window.destroy()"],
            capture_output=True, timeout=5,
        )
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def run_desktop_game(mode, maze, heuristic, seed, max_steps):
    validate(mode, maze, heuristic)
    random.seed(seed)
    engine = load_engine()
    try:
        import tkinter
        probe = tkinter.Tk()
        probe.withdraw()
        probe.destroy()
    except Exception as exc:
        raise DesktopWindowUnavailable("The desktop graphics window could not open.") from exc
    display_module = importlib.import_module("graphicsDisplay")
    display = display_module.PacmanGraphics(zoom=1.4, frameTime=0.12)
    state = new_state(engine, maze)
    if mode in SEARCH:
        actions, visits, _, _, _ = plan_route(engine, mode, state, maze, heuristic)
        class RouteAgent(engine.game.Agent):
            def getAction(self, state):
                return actions.pop(0) if actions else "Stop"
        agent = RouteAgent()
    elif mode == "play":
        agent = importlib.import_module("keyboardAgents").KeyboardAgent()
    else:
        agent = engine.searchAgents.GoWestAgent() if mode == "west" else custom_agent(engine)
    base_action = agent.getAction
    turns = [0]
    class Finished(Exception):
        pass
    def limited_action(state):
        if turns[0] >= max_steps:
            raise Finished()
        turns[0] += 1
        action = base_action(state)
        if mode == "west" and action == "Stop":
            raise Finished()
        return action
    agent.getAction = limited_action
    ghosts = [engine.ghostAgents.RandomGhost(i) for i in range(1, state.getNumAgents())]
    game = engine.pacman.ClassicGameRules().newGame(get_layout(engine, maze), agent, ghosts, display)
    try:
        game.run()
    except Finished:
        print("Demo finished. Close the window or run another program.")
    finally:
        display.finish()
