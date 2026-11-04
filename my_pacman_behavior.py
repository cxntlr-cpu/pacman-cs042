"""Your behavior rule. Change this file using the My Pacman prompt."""
from collections import deque

STEPS = {"North": (0, 1), "South": (0, -1), "East": (1, 0), "West": (-1, 0)}
DANGER_STEPS = 2  # flee when a normal ghost is this many steps away or closer


def choose_move(context, memory):
    """Return one of context['legal_moves']; memory lasts for one game.

    context: position (x,y), food [(x,y),...], ghosts [{position,scared}],
    capsules [(x,y),...], walls [(x,y),...], legal_moves [direction,...], score.
    Directions: 'North', 'South', 'East', 'West', 'Stop'.

    My rule: if a ghost that is not scared is 2 steps away or closer, run away
    from it. Otherwise walk toward the closest food (counting steps through the maze).
    """
    walls = {tuple(w) for w in context["walls"]}
    width, height = max(x for x, _ in walls), max(y for _, y in walls)
    me = tuple(context["position"])
    moves = [m for m in context["legal_moves"] if m != "Stop"]
    if not moves:
        return "Stop"

    # Steps from Pacman to every square, and the first move on the way there.
    dist, first = {me: 0}, {me: None}
    queue = deque([me])
    while queue:
        x, y = queue.popleft()
        for move, (dx, dy) in STEPS.items():
            nxt = (x + dx, y + dy)
            inside = 0 <= nxt[0] <= width and 0 <= nxt[1] <= height
            if inside and nxt not in walls and nxt not in dist:
                dist[nxt] = dist[(x, y)] + 1
                first[nxt] = first[(x, y)] or move
                queue.append(nxt)

    ghosts = [tuple(round(c) for c in g["position"]) for g in context["ghosts"] if not g["scared"]]
    near = [g for g in ghosts if dist.get(g, 99) <= DANGER_STEPS]
    if near:
        # Flee: pick the move that ends farthest from the closest dangerous ghost.
        def safety(move):
            x, y = me[0] + STEPS[move][0], me[1] + STEPS[move][1]
            return min(abs(x - gx) + abs(y - gy) for gx, gy in near)
        return max(moves, key=safety)

    food = [tuple(f) for f in context["food"] if tuple(f) in dist]
    if food:
        target = min(food, key=dist.get)
        if first[target] in moves:
            return first[target]
    return moves[0]


if __name__ == "__main__":
    open_maze = [(x, y) for x in range(7) for y in range(3) if y != 1]  # one corridor at y=1
    base = {"walls": open_maze, "capsules": [], "score": 0, "legal_moves": ["East", "West", "Stop"]}
    # Food to the east, no ghosts: go east.
    assert choose_move({**base, "position": (3, 1), "food": [(5, 1)], "ghosts": []}, {}) == "East"
    # Ghost 1 step east: flee west even though the food is east.
    ghost = [{"position": (4, 1), "scared": False}]
    assert choose_move({**base, "position": (3, 1), "food": [(5, 1)], "ghosts": ghost}, {}) == "West"
    # Same ghost but scared: ignore it and go for the food.
    scared = [{"position": (4, 1), "scared": True}]
    assert choose_move({**base, "position": (3, 1), "food": [(5, 1)], "ghosts": scared}, {}) == "East"
    print("my_pacman_behavior checks passed")
