from igraph import Graph
from typing import List
from igraph.clustering import VertexClustering

class Partition:
    def __init__(self):
        self._default_palette = None
        self._graph: Graph
        self._len = 0
        self._membership: List[int] = list()

def copy_partition(partition) -> VertexClustering:
    return VertexClustering(graph=partition._graph, membership=list(partition._membership))