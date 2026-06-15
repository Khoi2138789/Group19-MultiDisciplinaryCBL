import random
random.seed(0)

class Walker:
    """
    Controls a moving source node through the graph.
    """

    def __init__(self, graph, path):
        self.graph = graph
        self.path = path

        self.current = None

    def set_start(self, node):
        self.current = node
        self.path.visit(node)

    def step_random(self):
        neighbors = list(self.graph.neighbors(self.current))

        if not neighbors:
            return

        # bias: avoid high penalty nodes
        def score(n):
            return self.path.penalty(n)

        weights = []

        for node in neighbors:
            penalty = self.path.penalty(node)

            # convert penalty → desirability weight
            # (invert it)
            weight = node.value - penalty

            # avoid zero weights completely
            weight = max(weight, 0.0)

            weights.append(weight)

        total = sum(weights)

        next_node = None

        if (total == 0):
            next_node = random.choice(neighbors)
        else:
            next_node = random.choices(neighbors, weights=weights, k=1)[0]

        self.current = next_node
        self.path.visit(next_node)

        return next_node