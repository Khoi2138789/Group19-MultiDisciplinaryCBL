from collections import deque


class Path:
    """
    Stores traversal history with decay-based penalties.

    Key idea:
    - remembers last N visited nodes
    - assigns penalty based on recency
    - penalty fades to 0 after max memory window
    """

    def __init__(self, memory: int = 5):
        self.memory = memory

        # (node -> step_index)
        self.visited = {}

        # ordered history of nodes
        self.history = deque()

        self.step = 0

    def visit(self, node):
        """
        Record a visit to a node.
        """

        self.history.append(node)
        self.visited[node] = self.step

        self.step += 1

        # enforce memory limit
        while len(self.history) > self.memory:
            old = self.history.popleft()
            self.visited.pop(old, None)

    def penalty(self, node) -> float:
        """
        Returns penalty based on recency.

        Newest = highest penalty
        Old = fades to 0
        """

        if node not in self.visited:
            return 0.0

        age = self.step - self.visited[node]

        if age > self.memory:
            return 0.0

        # linear decay
        return 2.0 - (age / (self.memory + 1))

    def contains(self, node) -> bool:
        return node in self.visited