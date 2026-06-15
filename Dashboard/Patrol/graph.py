from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Set, Tuple, Optional, Iterable
import uuid

@dataclass(eq=False)
class Node:
    """
    A robust graph node.

    Features:
    - Unique immutable ID
    - Arbitrary numeric value
    - Position for visualization
    - Metadata storage
    - Hashable / usable in sets & dicts
    """

    value: float
    lat: float
    lon: float

    metadata: dict = field(default_factory=dict)

    _id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __hash__(self) -> int:
        return hash(self._id)

    def __eq__(self, other) -> bool:
        return isinstance(other, Node) and self._id == other._id

    @property
    def id(self) -> str:
        return self._id
    
    @property
    def x(self):
        return self.lon * 1000

    @property
    def y(self):
        return -self.lat * 1000

    def set_position(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    def __repr__(self) -> str:
        return f"Node(id={self._id[:16]}, value={self.value})"


class Graph:
    """
    Undirected graph implementation.

    Uses adjacency sets:
        node -> connected nodes
    """

    def __init__(self) -> None:
        self._nodes: Dict[str, Node] = {}
        self._adjacency: Dict[Node, Set[Node]] = {}

    # -----------------------------------------------------
    # NODE MANAGEMENT
    # -----------------------------------------------------

    def add_node(self, node: Node) -> None:
        if node.id in self._nodes:
            raise ValueError("Node already exists in graph.")

        self._nodes[node.id] = node
        self._adjacency[node] = set()

    def remove_node(self, node: Node) -> None:
        if node not in self._adjacency:
            return

        # Remove all edges connected to node
        for neighbor in self._adjacency[node]:
            self._adjacency[neighbor].remove(node)

        del self._adjacency[node]
        del self._nodes[node.id]


    def add_edge(self, a: Node, b: Node) -> None:
        self._ensure_nodes_exist(a, b)

        if a == b:
            raise ValueError("Self-loops are not allowed.")

        if b not in self._adjacency[a]:
            self._adjacency[a].add(b)
            self._adjacency[b].add(a)

    def remove_edge(self, a: Node, b: Node) -> None:
        self._ensure_nodes_exist(a, b)

        self._adjacency[a].discard(b)
        self._adjacency[b].discard(a)

    def neighbors(self, node: Node) -> Set[Node]:
        self._ensure_nodes_exist(node)
        return set(self._adjacency[node])

    def has_edge(self, a: Node, b: Node) -> bool:
        self._ensure_nodes_exist(a, b)
        return b in self._adjacency[a]

    @property
    def nodes(self) -> Tuple[Node, ...]:
        return tuple(self._nodes.values())

    @property
    def edges(self) -> Set[Tuple[Node, Node]]:
        result = set()

        for node, neighbors in self._adjacency.items():
            for neighbor in neighbors:
                edge = tuple(sorted((node, neighbor), key=lambda n: n.id))
                result.add(edge)

        return result

    def node_count(self) -> int:
        return len(self._nodes)

    def edge_count(self) -> int:
        return len(self.edges)

    def _ensure_nodes_exist(self, *nodes: Node) -> None:
        for node in nodes:
            if node not in self._adjacency:
                raise ValueError(f"Node not in graph: {node}")

    def __repr__(self) -> str:
        return (
            f"Graph(nodes={self.node_count()}, "
            f"edges={self.edge_count()})"
        )