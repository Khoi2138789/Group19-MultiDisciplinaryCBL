from Dashboard.Patrol.graph import Graph, Node
from Dashboard.Patrol.vis import GraphRenderer
from Dashboard.Patrol.path import Path
from Dashboard.Patrol.walker import Walker

import random
from math import sqrt

from scipy.spatial import Delaunay

import pygame

pygame.display.set_mode((1920, 1080), pygame.RESIZABLE)


graph = Graph()

nodes = []
GRID_SIZE = 10
SPACING = 150

center = (GRID_SIZE - 1) // 2

N_NODES = 150
SPREAD = 1000


graph = Graph()
nodes = []

# # -----------------------------------------
# # 1. CREATE RANDOM POINTS (NODES)
# # -----------------------------------------

# for _ in range(N_NODES):
#     node = Node(
#         value=random.random(),  # already in [0,1]
#         x=random.uniform(-SPREAD, SPREAD),
#         y=random.uniform(-SPREAD, SPREAD),
#     )

#     graph.add_node(node)
#     nodes.append(node)

# # -----------------------------------------
# # 2. DELAUNAY TRIANGULATION
# # -----------------------------------------

# points = [(n.x, n.y) for n in nodes]
# tri = Delaunay(points)

# # -----------------------------------------
# # 3. BUILD EDGES (PLANAR GRAPH)
# # -----------------------------------------

# for simplex in tri.simplices:
#     for i in range(3):
#         a = nodes[simplex[i]]
#         b = nodes[simplex[(i + 1) % 3]]

#         graph.add_edge(a, b)

# # -----------------------------------------
# # 4. RUN VISUALIZER
# # -----------------------------------------


data = [
    {
        "id": "1",
        "value": 0.2,
        "lat": 52.0705,
        "lon": 4.3007,
        "neighbors": ["2"]
    },
    {
        "id": "2",
        "value": 0.5,
        "lat": 52.0800,
        "lon": 4.3100,
        "neighbors": ["1"]
    }
]

graph = Graph()
nodes_by_id = {}

# create nodes
for item in data:
    node = Node(
        _id=item["id"],
        value=item["value"],
        lat=item["lat"],
        lon=item["lon"]
    )

    graph.add_node(node)
    nodes_by_id[node.id] = node

# connect nodes
for item in data:
    source = nodes_by_id[item["id"]]

    for nid in item["neighbors"]:
        target = nodes_by_id[nid]
        graph.add_edge(source, target)

path = Path(memory=10)
walker = Walker(graph, path)

start = nodes_by_id["1"]

walker.set_start(start)

# -----------------------------------------
# RENDERER
# -----------------------------------------

renderer = GraphRenderer(graph)
renderer.attach_simulation(walker, path)
renderer.centre_screen_to_node(start)

# -----------------------------------------
# MAIN LOOP WRAP
# -----------------------------------------

clock = pygame.time.Clock()
running = True

while running:

    renderer.handle_events()
    renderer.draw()

    clock.tick(60)

pygame.quit()