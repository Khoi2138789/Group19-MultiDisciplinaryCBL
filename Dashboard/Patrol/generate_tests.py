import os
import json

import numpy as np
import random

from graph import Graph, Node
from path import Path
from walker import Walker

random.seed(0)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(BASE_DIR, '../lsoa_by_pfa.json')) as f:
    PFA_DATA = json.load(f)

print("generating tests")

patrol_length = 1_000_000

lsoa_score = {}

for pfa_name, lsoas in PFA_DATA.items():

    print(f'walking pfa: {pfa_name}')

    graph = Graph()

    nodes_by_id = {}

    for item in lsoas:

        code = item.get("lsoa_code")
        score = item.get("z_score", 0.0)
        lat = item.get("lat")
        lon = item.get("long")

        if not all([code, lat, lon]):
            continue

    for item in lsoas:

        node = Node(
            _id=item["lsoa_code"],
            value=1 / (1 + np.exp(-item["z_score"])),
            lat=item["lat"],
            lon=item["long"]
        )

        graph.add_node(node)
        nodes_by_id[node.id] = node

    pfa_lsoas = set(item["lsoa_code"] for item in lsoas)

    for item in lsoas:
        source = nodes_by_id[item["lsoa_code"]]

        for nid in item["neighbours"]:
            if nid not in pfa_lsoas:
                continue
            target = nodes_by_id[nid]
            graph.add_edge(source, target)
    
    path = Path(memory=5)

    walker = Walker(graph, path)
    values_iter = iter(nodes_by_id.values())
    start = next(values_iter)
    walker.set_start(start)

    critical_node_count = 0
    
    for i in range(patrol_length):
        n = walker.step_random()

        if n is None:
            continue

        critical_node_count+=n.value

    lsoa_score[pfa_name] = critical_node_count / patrol_length

with open("test_results.json", "w") as f:
    json.dump(lsoa_score, f, indent=2)
    