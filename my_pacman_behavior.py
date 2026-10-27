"""Your behavior rule. Change this file using the My Pacman prompt."""


def choose_move(context, memory):
    """Return one of context['legal_moves']; memory lasts for one game.

    context: position (x,y), food [(x,y),...], ghosts [{position,scared}],
    capsules [(x,y),...], walls [(x,y),...], legal_moves [direction,...], score.
    Directions: 'North', 'South', 'East', 'West', 'Stop'.
    The starter prefers west, then south, then east, then north. It can loop!
    """
    for direction in ("West", "South", "East", "North", "Stop"):
        if direction in context["legal_moves"]:
            return direction
    return "Stop"
