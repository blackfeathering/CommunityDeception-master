import logging.config
from typing import List
from settings import master
from igraph import Graph
import random
from igraph.clustering import VertexClustering
from math import log
from utils.timer import time_mark
import time
import matplotlib.pyplot as plt

logging.config.dictConfig(master.LOGGING_SETTINGS)
logger = logging.getLogger('normal')


class ctrperCombine(object):
    def __init__(self, graph, edges_sum, detection_func, func_args, interval, partitions=None,
                 path=None, index0=3, index1=0, **kwargs):
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

        logger.info("ctrperCombine")
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

        # 最终合并的社区编号为self.__community_index_1
        partation_expected = VertexClustering(graph=self.__partitions._graph,
                                              membership=list(self.__partitions._membership))
        for i in range(len(partation_expected._membership)):
            if partation_expected._membership[i] == self.__community_index_0:
                partation_expected._membership[i] = self.__community_index_1
        for i in range(len(partation_expected._membership)):
            if partation_expected._membership[i] == partation_expected._len - 1:
                partation_expected._membership[i] = self.__community_index_0
        partation_expected._len -= 1
        # print(partation_expected._membership)
        self.__partitions_expected = partation_expected

        # for i in range(0, 11):
        #    print(self.__partitions.subgraph(i).vcount())
        # for i in range(0, 10):
        #    print(self.__partitions_expected.subgraph(i).vcount())

    def __combine(self):
        # 求两个子图顶点集合
        vertex_list0 = list()  # ((degree,index))
        vertex_list1 = list()
        for index in range(len(self.__vertex_part)):
            if self.__vertex_part[index] == 0:
                vertex_list0.append(self.__vertex_list[index])
            if self.__vertex_part[index] == 1:
                vertex_list1.append(self.__vertex_list[index])
        after_graph = self.__graph.copy()
        # 建立子图与顶点集的对应关系（graph.subgraph(vlist)新顶点的顺序与原来的不变）
        vertex_list0.sort()
        vertex_list1.sort()
        g0 = after_graph.subgraph(vertex_list0)
        g1 = after_graph.subgraph(vertex_list1)
        # 寻找两个子图的中心点
        index0 = g0.eccentricity().index(min(g0.eccentricity()))
        index1 = g1.eccentricity().index(min(g1.eccentricity()))
        # 合并两子图（从原图再抽出）g1+g2+e
        g_after = after_graph.subgraph(self.__vertex_list)
        listvg = self.__vertex_list.copy()
        listvg.sort()
        g_after.add_edge(listvg.index(vertex_list0[index0]), listvg.index(vertex_list1[index1]))

        fname = master.GRAPH_SETTINGS['path'][8:len(master.GRAPH_SETTINGS['path'])]
        f = open('test/{}_{}_ctrperadd.txt'.format(fname, master.GRAPH_SETTINGS['edges_sum']), 'w')
        # 首先连接中心点
        edgeadd = (vertex_list0[index0], vertex_list1[index1])
        after_graph.add_edge(edgeadd[0], edgeadd[1])
        self.__edge_set.add(edgeadd)
        s = '(' + str(edgeadd[0]) + ',' + str(edgeadd[1]) + ')' + '\n'
        f.write(s)
        # 循环添加最远对
        for i in range(1, self.__edges_sum):
            d = g_after.diameter()
            ld = g_after.shortest_paths_dijkstra()
            for index, value in enumerate(ld):
                for index1, value1 in enumerate(value):
                    if value1 == d:
                        edadd = (index, index1)
                        break
                else:
                    continue
                break
            #print(edgeadd)
            g_after.add_edge(edadd[0], edadd[1])
            edgeadd = (listvg[edadd[0]], listvg[edadd[1]])
            if edgeadd not in self.__edge_set:
                after_graph.add_edge(edgeadd[0], edgeadd[1])
                self.__edge_set.add(edgeadd)
                s = '(' + str(edgeadd[0]) + ',' + str(edgeadd[1]) + ')' + '\n'
                f.write(s)
        f.close()

    def __evaluation_log(self, after_graph):
        temp_partitions = master.GRAPH_SETTINGS['detection_func'](after_graph, **master.GRAPH_SETTINGS['func_args'])
        # print(temp_partitions._membership)
        set_x = set(self.__vertex_list)
        # print(set_x)
        set_yi = set()
        ideal_evaluation = float(0)
        mem = temp_partitions._membership
        for i in range(0, temp_partitions._len):
            set_yi.clear()
            eva = float(0)
            for index in range(len(mem)):
                if mem[index] == i:
                    set_yi.add(index)
            # print(set_yi)
            xx = len(set_x.intersection(set_yi))
            if xx != 0:
                eva = xx / len(set_x) * log(xx / len(set_x), 2)
                ideal_evaluation += eva

        return ideal_evaluation

    def run(self):
        self.__preprocess()
        self.__start()
        self.__combine()
        self.__quit()
