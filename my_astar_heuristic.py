"""Your A* estimate. Change this file using the My heuristic prompt."""


def estimate(position, goal):
    """Estimate remaining travel cost; coordinates are (x, y), bottom-left origin.

    The starter is Manhattan distance: horizontal steps + vertical steps.
    Each step in our search mazes costs at least 1, so this never overestimates.
    """
    x, y = position
    goal_x, goal_y = goal
    return abs(x - goal_x) + abs(y - goal_y)
