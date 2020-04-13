import logging.config
import sys
import cmath
from typing import List
from settings import master
from igraph import Graph
from igraph.clustering import VertexClustering
from utils.counter_pre import count_security_index_by_pre
from utils.pre_counter import count_pre_security_index
from utils.counter import count_security_index

from utils.timer import time_mark
import time

logging.config.dictConfig(master.LOGGING_SETTINGS)
logger = logging.getLogger('normal')


class CommunityCombine(object):
    def __init__(self, graph, edges_sum, detection_func, func_args, interval, partitions=None,
                 path=None, index0=1, index1=0, **kwargs):
        self.__graph = graph
        self.__edges_sum = edges_sum
        self.__detection_func = detection_func
        self.__func_args = func_args
        self.__interval = interval
        self.__partitions = partitions
        self.__path = path

        self.__community_index_0 = index0
        self.__community_index_1 = index1
        self.__edge_set = None
        self.__degree_list = None
        self.__vertex_list = None
        self.__vertex_part = None
        self.__edge_added_list = None

        self.__partitions_expected = None
        self.__partitions_expected_degree: List[int] = list()
        self.__partitions_expected_volume: List[int] = list()
        self.__sorted_partitions_expected: List[List[int]] = list()
        self.__degree_distribute: List[int] = list()

        self.__start_time = time.time()
        self.__end_time = None

    def __start(self):

        logger.info("CommunityCombine")
        logger.info(f'Time : {time_mark(self.__start_time)}')
        logger.info(f'Graph: {self.__path}')
        logger.info(f'Info : {self.__graph.vcount()} {self.__graph.ecount()}')
        logger.info(f'Edges: {self.__edges_sum}')
        logger.info(f'Func : {self.__detection_func.__name__}')
        logger.info(f'Args : {self.__func_args}')
        logger.info(f'Gap  : {self.__interval}')
        logger.info(f'Parts: {len(self.__partitions)}')
        logger.info("Community1")

        subgraph0 = self.__partitions.subgraph(self.__community_index_0)
        logger.info(f'Community index: {self.__community_index_0},  '
                    f'Info : {subgraph0.vcount()} {subgraph0.ecount()}')
        logger.info("Community2")
        subgraph1 = self.__partitions.subgraph(self.__community_index_1)
        logger.info(f'Community index: {self.__community_index_1},  '
                    f'Info : {subgraph1.vcount()} {subgraph1.ecount()}')
        logger.info("=" * 60)

    def __quit(self):
        self.__end_time = time.time()
        logger.info("=" * 60)
        logger.info(f'Time : {time_mark(self.__end_time)}')
        logger.info(f'Total: {(self.__end_time - self.__start_time):10.4f} s')
        logger.info("=" * 60)
        logger.info("\n\n")

    def __preprocess(self):
        self.__edge_set = set(self.__graph.get_edgelist())
        if not self.__partitions:
            self.__partitions = self.__detection_func(self.__graph, **self.__func_args)
        self.__set_necessary_info()


    def __set_necessary_info(self):
        v_degree = list()
        v_index = list()
        v_partation = list()
        memberships = self.__partitions._membership
        for index in range(len(memberships)):
            if memberships[index] == self.__community_index_0:
                v_index.append(index)
                v_degree.append(self.__graph.degree(index))
                v_partation.append(0)
            if memberships[index] == self.__community_index_1:
                v_index.append(index)
                v_degree.append(self.__graph.degree(index))
                v_partation.append(1)

        self.__degree_list = v_degree
        self.__vertex_list = v_index
        self.__vertex_part = v_partation

        partation_expected = VertexClustering(graph=self.__partitions._graph, membership=list(self.__partitions._membership))
        for i in range(len(partation_expected._membership)):
            if partation_expected._membership[i] == self.__community_index_0:
                partation_expected._membership[i] = self.__community_index_1
        for i in range(len(partation_expected._membership)):
            if partation_expected._membership[i] == partation_expected._len - 1:
                partation_expected._membership[i] = self.__community_index_0
        partation_expected._len -= 1

        self.__partitions_expected = partation_expected

        # for i in range(0, 11):
        #    print(self.__partitions.subgraph(i).vcount())
        # for i in range(0, 10):
        #    print(self.__partitions_expected.subgraph(i).vcount())

        for index, part in enumerate(self.__partitions_expected):
            subgraph: Graph = self.__partitions_expected.subgraph(index)
            self.__partitions_expected_degree.append(2 * subgraph.ecount())
            self.__partitions_expected_volume.append(sum(self.__graph.degree(part)))
            # self.__sorted_partitions_expected.append(sorted(part, key=lambda x: self.__graph.degree(x)))

    def __combine(self):
        Max_vertex0 = self.__vertex_list[self.__degree_list.index(max(self.__degree_list))]
        Max_part0 = self.__vertex_part[self.__vertex_list.index(Max_vertex0)]
        vertex_part1 = Max_part0 ^ 1
        vertex_list0 = list()   # ((degree,index))
        vertex_list1 = list()
        for index in range(len(self.__vertex_part)):
            if self.__vertex_part[index] == Max_part0:
                vertex_list0.append((self.__degree_list[index], self.__vertex_list[index]))
            if self.__vertex_part[index] == vertex_part1:
                vertex_list1.append((self.__degree_list[index], self.__vertex_list[index]))
        vertex_list0.sort(reverse=True, key=lambda x: x[0])
        vertex_list1.sort(reverse=True, key=lambda x: x[0])
        # print(vertex_list0)
        # print(vertex_list1)
        after_graph = self.__graph.copy()
        edge_set = set()
        vertex_set = set(self.__vertex_list)
        for ed in self.__edge_set:
            if ed[0] in vertex_set and ed[1] in vertex_set:
                edge_set.add(ed)

        degree_distribute = after_graph.degree(after_graph.vs)
        membership = self.__partitions_expected._membership
        total_degree = 2 * after_graph.ecount()

        # ideal_evaluation = self.__evaluation(after_graph)
        # logger.info(f"index: ({ideal_evaluation:8.7f})")
        # ideal_evaluation = self.__evaluation(after_graph)
        # logger.info(f"index: ({ideal_evaluation:8.7f})")
        # ideal_evaluation = self.__evaluation(after_graph)
        # logger.info(f"index: ({ideal_evaluation:8.7f})")
        # logger.info("=" * 10)

        for i in range(0, self.__edges_sum):
            edgeadd = self.__enum_add_edge(vertex_list0, vertex_list1, after_graph, self.__partitions_expected, membership,
                                           total_degree, degree_distribute)
            if edgeadd not in self.__edge_set:
                after_graph.add_edge(edgeadd[0], edgeadd[1])
                # print(len(self.__edge_set))
                self.__edge_set.add(edgeadd)
                # print(edgeadd)
                self.__partitions_expected_volume[membership[edgeadd[0]]] += 1
                self.__partitions_expected_volume[membership[edgeadd[1]]] += 1
                # degree_distribute[edgeadd[0]] += 1
                # degree_distribute[edgeadd[1]] += 1
                total_degree += 2
                # print(len(self.__edge_set))
            # if (i + 1) % 10 == 0:
                ideal_evaluation = self.__evaluation(after_graph)
                logger.info(f"index: ({ideal_evaluation:8.7f})")
                ideal_evaluation = self.__evaluation(after_graph)
                logger.info(f"index: ({ideal_evaluation:8.7f})")
                ideal_evaluation = self.__evaluation(after_graph)
                logger.info(f"index: ({ideal_evaluation:8.7f})")
                logger.info("=" * 10)

    def __enum_add_edge(self, vertex_list0, vertex_list1, graph, partitions, membership, total_degree, degree_distribute):
        Max_scurty = (0, 0, 0)
        edge_add = (0, 0)
        v0 = (0, 0)
        v1 = (0, 0)
        pre_count = count_pre_security_index(graph, partitions, self.__partitions_expected_degree,
                                             self.__partitions_expected_volume)

        for i in vertex_list0:
            for j in vertex_list1:
                if (i[1], j[1]) not in self.__edge_set and (j[1], i[1]) not in self.__edge_set:
                    # temp_graph = graph.copy()
                    edge_add = (i[1], j[1])
                    # temp_graph.add_edge(i[1], j[1])
                    src_des = (membership[edge_add[0]], membership[edge_add[1]])
                    xx = count_security_index_by_pre(pre_count, edge_add, src_des, total_degree + 2,
                                                     self.__partitions_expected_degree,
                                                     self.__partitions_expected_volume, degree_distribute)
                    if xx[0] > Max_scurty[0]:
                        Max_scurty = xx
                        v0 = (i[0], i[1])
                        v1 = (j[0], j[1])
                        edgeadd = (i[1], j[1])

        # print(edgeadd)
        # print(v0, v1, Max_scurty)
        logger.info(f"edge added: {v0[1], v1[1]}, dergee: {v0[0], v1[0]}, security index: ({Max_scurty[0]:8.7f}),"
                    f" resistance: ({Max_scurty[1]:8.7f}), position_entropy: ({Max_scurty[2]:8.7f})")
        return edgeadd

    def __evaluation(self, after_graph):
        temp_partitions = master.GRAPH_SETTINGS['detection_func'](after_graph, **master.GRAPH_SETTINGS['func_args'])
        set_x = set(self.__vertex_list)
        set_yi = set()
        ideal_evaluation = float(0)
        mem = temp_partitions._membership
        for i in range(0, temp_partitions._len):
            set_yi.clear()
            for index in range(len(mem)):
                if mem[index] == i:
                    set_yi.add(index)
            xx = len(set_x.intersection(set_yi)) / ((len(set_x) * len(set_yi)) ** 0.5)
            if xx > ideal_evaluation:
                ideal_evaluation = xx
        return ideal_evaluation

    def __edge_add(self, vertex_list0, vertex_list1, Max_vertex0):
        for vertex_target in vertex_list1:
            edge_target = (vertex_target[1], Max_vertex0)
            edge_target1 = (Max_vertex0, vertex_target[1])
            if edge_target not in self.__edge_set and edge_target1 not in self.__edge_set:
                break
        for vertex_target in vertex_list0:
            if edge_target1[0] == vertex_target[1]:
                vertex000 = vertex_target
                break
        for vertex_target in vertex_list1:
            if edge_target1[1] == vertex_target[1]:
                vertex111 = vertex_target
                break
        Max_sumdegree = vertex000[0] + vertex111[0]
        Min_disdegree = abs(vertex000[0] - vertex111[0])
        for i in vertex_list0:
            for j in vertex_list1:
                if (i[1], j[1]) not in self.__edge_set and (j[1], i[1]) not in self.__edge_set:
                    if i[0] + j[0] > Max_sumdegree:
                        Max_sumdegree = i[0] + j[0]
                        Min_disdegree = abs(i[0] - j[0])
                        vertex000 = i
                        vertex111 = j
                    if i[0] + j[0] == Max_sumdegree:
                        if abs(i[0] - j[0]) < Min_disdegree:
                            Min_disdegree = abs(i[0] - j[0])
                            vertex000 = i
                            vertex111 = j
                    if i[0] + j[0] < Max_sumdegree:
                        break
        edge_target = (vertex000[1], vertex111[1])
        logger.info(f"edge: {vertex000[1], vertex111[1]}, dergee: {vertex000[0], vertex111[0]}")
        return edge_target

    def run(self):
        self.__preprocess()
        self.__start()
        self.__combine()
        self.__quit()
