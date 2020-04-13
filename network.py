import networkx as nx
from igraph import Graph
from igraph.clustering import VertexClustering
#from utils.convert import networkx2igraph


def __gaussian_random_partition_graph(l, s, v, k, sigma):
    k = k / 2
    z_in = k * sigma
    z_out = k - z_in
    n = s * l

    p_in = z_in / (s - 1)
    p_out = z_out / (n - s)

    if v:
        v = s / (v ** 2)
    else:
        v = float('inf')

    return nx.generators.gaussian_random_partition_graph(n, s, v, p_in, p_out).to_undirected()


def __check_graph(nx_graph, ig_graph, l, s, v, k, sigma):
    assert not ig_graph.is_directed()
    assert not any(ig_graph.is_multiple())
    assert ig_graph.is_connected()
    assert ig_graph.vcount() == nx_graph.number_of_nodes()
    assert ig_graph.ecount() == nx_graph.number_of_edges()
    assert ig_graph.vcount() == l * s
    assert len(set(ig_graph.vs['part'])) == l


def gaussian_random_partition_graph(l, s, v, k, sigma, output_path=None):
    """
    :param l: number of communities
    :param s: average community size
    :param v: standard deviation of community size
    :param k: average degree of any node
    :param sigma: separation degree
    :param output_path: gml file output path
    :return: igraph.Graph
    """
    try_count = 0

    while True:
        if not try_count % 10:
            print(f"try {try_count + 1} to generate {l}_{s}_{v}_{k}_{sigma}")

        graph: nx.Graph = __gaussian_random_partition_graph(l, s, v, k, sigma)
        new_graph = networkx_to_igraph(graph)

        try:
            __check_graph(graph, new_graph, l, s, v, k, sigma)
        except AssertionError:
            try_count += 1
            continue
        except Exception as e:
            print(e)
        else:
            print(f"Total try {try_count + 1} times to generate {l}_{s}_{v}_{k}_{sigma}")
            break

    if not output_path:
        return new_graph
    else:
        file_name = f"{l}_{s}_{v}_{k}_{sigma}.gml"
        with open(output_path + "/" + file_name, "wb") as file:
            new_graph.write_gml(file)

    return new_graph


def lfr_benchmark_graph(n, tau1, tau2, mu, average_degree, min_community, output_path=None):
    nx_graph = nx.generators.LFR_benchmark_graph(n, tau1, tau2, mu, average_degree=average_degree
                                                 , min_community=min_community)
    communities = {frozenset(nx_graph.nodes[v]['community']) for v in nx_graph}
    membership = [0] * nx_graph.number_of_nodes()

    for index, part in enumerate(communities):
        for v in part:
            membership[v] = index

    ig_graph = networkx_to_igraph(nx_graph)
    ig_graph.vs['part'] = membership

    assert not ig_graph.is_directed()
    assert not any(ig_graph.is_multiple())
    assert ig_graph.is_connected()
    assert ig_graph.vcount() == nx_graph.number_of_nodes()
    assert ig_graph.ecount() == nx_graph.number_of_edges()

    if not output_path:
        return ig_graph
    else:
        file_name = output_path
        with open(file_name, "wb") as file:
            ig_graph.write_gml(file)

    return ig_graph


def networkx_to_igraph(nx_graph: nx.Graph):
    ig_graph = Graph(
        n=nx_graph.number_of_nodes(),
        edges=list(nx_graph.edges()),
        directed=False,
    )

    blocks = list(i[1] for i in nx_graph.nodes(data="block"))
    add_part_to_graph(ig_graph, blocks)

    return ig_graph


def add_part_to_graph(graph: Graph, membership: list, part_name="part", inplace=True):
    if inplace:
        graph.vs[part_name] = membership
        return None

    else:
        temp_graph = graph.copy()
        temp_graph.vs[part_name] = membership
        return temp_graph


def desc(graph: Graph):
    parts = VertexClustering(graph, [int(i) for i in graph.vs['part']])
    print(graph.vcount(), graph.ecount())
    print(f"Part Num: {len(parts)}")
    print(f"Part Size: {[len(part) for part in parts]}")
    print(f"Modularity: {parts.modularity}")
    in_edges = 0
    for subgraph in parts.subgraphs():
        in_edges += subgraph.ecount()

    print(f"fraction: {in_edges / graph.ecount()}")
    print("Degree Distribution: ")
    print(graph.degree_distribution())


if __name__ == '__main__':
    #graph = gaussian_random_partition_graph(10, 50, 1, 15, 0.9, '../samples')
    graph = lfr_benchmark_graph(500, 2.5, 1.5, 0.9, 5, 10, "../samples/500_5_2.5_1.5_10_0.9.gml")
    #from utils.graph import desc

    desc(graph)