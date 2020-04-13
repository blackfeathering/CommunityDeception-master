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

class NewtestCommunityCombine(object):
    def __init__(self, graph, edges_sum, detection_func, func_args, interval, partitions=None,
                 path=None, index0=2, index1=0, **kwargs):
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

        if self.__community_index_0 > self.__community_index_1:
            a = self.__community_index_1
            self.__community_index_1 = self.__community_index_0
            self.__community_index_0 = a

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
        partation_expected = VertexClustering(graph=self.__partitions._graph, membership=list(self.__partitions._membership))
        for i in range(len(partation_expected._membership)):
            if partation_expected._membership[i] == self.__community_index_1:
                partation_expected._membership[i] = self.__community_index_0
        for i in range(len(partation_expected._membership)):
            if partation_expected._membership[i] == partation_expected._len - 1:
                partation_expected._membership[i] = self.__community_index_1
        partation_expected._len -= 1
        #print(partation_expected._membership)
        self.__partitions_expected = partation_expected


