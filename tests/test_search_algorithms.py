"""Behavior checks, not algorithm implementations. Unbuilt searches are skipped."""
import unittest

from pacman_app.download_berkeley_project import ensure_engine
from pacman_app.game_runner import SEARCH, load_engine, readiness, simulate


class Graph:
    def __init__(self, edges, start="S", goal="G"):
        self.edges, self.start, self.goal = edges, start, goal

    def getStartState(self):
        return self.start

    def isGoalState(self, state):
        return state == self.goal

    def getSuccessors(self, state):
        return [(target, (state, target), cost) for target, cost in self.edges.get(state, [])]

    def getCostOfActions(self, actions):
        state, total = self.start, 0
        for source, target in actions:
            if source != state:
                raise AssertionError("The actions do not form a connected route.")
            choices = dict(self.edges.get(source, []))
            if target not in choices:
                raise AssertionError("The route uses an edge that does not exist.")
            total += choices[target]
            state = target
        return total


class SearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_engine()
        cls.engine = load_engine()

    def exercise(self, mode):
        if not readiness()[mode]:
            self.skipTest(f"{mode.upper()} not built yet — use its prompt first")
        fn = getattr(self.engine.search, SEARCH[mode])
        solve = (lambda problem: fn(problem, heuristic=lambda state, problem: 0)) if mode == "astar" else fn
        graph = Graph({"S": [("A", 4), ("B", 1)], "A": [("S", 1), ("G", 1)],
                       "B": [("A", 1), ("G", 10)]})
        route = solve(graph)
        self.assertIsInstance(route, list)
        self.assertTrue(route)
        self.assertEqual(route[-1][1], "G")
        cost = graph.getCostOfActions(route)
        if mode == "bfs":
            self.assertEqual(len(route), 2, "BFS must find the fewest edges.")
        if mode in ("ucs", "astar"):
            self.assertEqual(cost, 3, "A cheaper path to A must replace the earlier expensive one.")
        self.assertEqual(solve(Graph({"S": [("A", 1)], "A": [("S", 1)]})), [], "A cycle with no goal must terminate.")
        self.assertEqual(solve(Graph({}, start="G")), [], "An already-reached goal needs no moves.")
        zero = Graph({"S": [("A", 0), ("G", 2)], "A": [("S", 0), ("G", 1)]})
        zero_route = solve(zero)
        self.assertEqual(zero_route[-1][1], "G")
        if mode in ("ucs", "astar"):
            self.assertEqual(zero.getCostOfActions(zero_route), 1)
        if mode == "astar":
            graph = Graph({"S": [("A", 3), ("B", 1)], "A": [("G", 3)], "B": [("A", 1)]})
            h = {"S": 5, "A": 0, "B": 4, "G": 0}  # Admissible, but inconsistent.
            route = fn(graph, heuristic=lambda state, problem: h[state])
            self.assertEqual(graph.getCostOfActions(route), 5, "A* must reopen A when its path becomes cheaper.")
        result = simulate(mode, "tiny")
        self.assertTrue(result["won"], "The actual Berkeley maze must also finish.")

    def test_dfs(self):
        self.exercise("dfs")

    def test_bfs(self):
        self.exercise("bfs")

    def test_ucs(self):
        self.exercise("ucs")

    def test_astar(self):
        self.exercise("astar")


if __name__ == "__main__":
    unittest.main()
