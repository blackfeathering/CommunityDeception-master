from math import log


def __count_position_entropy(graph, vertex_list):
    total_degree = 2 * graph.ecount()
    position_entropy = 0

    for i in vertex_list:
        var = graph.vs[i].degree() / total_degree
        position_entropy += var * log(var, 2)

    return position_entropy


def __count_resistance(graph, vertex_list, g):
    total_degree = 2 * graph.ecount()
    resistance = 0

    var = 0
    for i in vertex_list:
        var += graph.vs[i].degree()

    resistance = (var - g)/total_degree * log(var/total_degree, 2)

    return resistance


def count_security_index(graph, vertex_list, g):
    position_entropy = __count_position_entropy(graph, vertex_list)
    resistance = __count_resistance(graph, vertex_list, g)
    security_index = resistance / position_entropy

    return security_index
