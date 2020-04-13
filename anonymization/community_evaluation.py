import logging.config
from typing import List
from settings import master
from igraph.clustering import VertexClustering
from utils.timer import time_mark
import time
import re
from math import log
import matplotlib.pyplot as plt

logging.config.dictConfig(master.LOGGING_SETTINGS)
logger = logging.getLogger('normal')


class CommunityEvaluation(object):
    def __init__(self, graph, edges_sum, detection_func, func_args, interval, partitions=None,
                 path=None, index0=3, index1=0, ffname='fastadd', **kwargs):
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

        self.__name = ffname

    def __start(self):

        logger.info("Communityevaluation")
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


    def __process(self):
        fname = master.GRAPH_SETTINGS['path'][8:len(master.GRAPH_SETTINGS['path'])]
        with open('test/{}_{}_{}.txt'.format(fname, master.GRAPH_SETTINGS['edges_sum'], self.__name), 'r') as f:
            list1 = f.readlines()

        fw = open('test/{}_{}_{}_evaluation.txt'.format(fname, master.GRAPH_SETTINGS['edges_sum'], self.__name), 'w')
        after_graph = self.__graph
        eva = float(0)
        for i in range(0,50):
            eva += self.__evaluation(after_graph)
        eva /= 50
        fw.write(str(eva)+'\n')
        #y_data = list()
        #y_data.append(eva)
        count = 1
        edgesum = int(master.GRAPH_SETTINGS['edges_sum'])
        x = 1
        if edgesum >= 100:
            x = 10
        if edgesum >= 1000:
            x = 100
        for line in list1:
            num = re.findall(r"\d+\.?\d*", line)
            after_graph.add_edge(int(num[0]), int(num[1]))
            if count % x == 0:
                eva = float(0)
                for i in range(0, 50):
                    eva += self.__evaluation(after_graph)
                eva /= 50
                #logger.info(f"evaluation: ({eva:8.7f})")
                fw.write(str(eva) + '\n')
            count += 1
            #print(after_graph.ecount())
            #y_data.append(eva)

        fw.close()
        #x_data = [i for i in range(0, master.GRAPH_SETTINGS['edges_sum']+1)]
        #plt.plot(x_data, y_data)
        #plt.title(self.__name)
        #plt.show()


    def __evaluation(self, after_graph):
        temp_partitions = master.GRAPH_SETTINGS['detection_func'](after_graph, **master.GRAPH_SETTINGS['func_args'])
        # print(temp_partitions._membership)
        set_x = set(self.__vertex_list)
        # print(set_x)
        set_yi = set()
        ideal_evaluation = float(0)
        mem = temp_partitions._membership
        for i in range(0, temp_partitions._len):
            set_yi.clear()
            for index in range(len(mem)):
                if mem[index] == i:
                    set_yi.add(index)
            # print(set_yi)
            xx = len(set_x.intersection(set_yi)) / ((len(set_x) * len(set_yi)) ** 0.5)
            # print(xx)
            if xx > ideal_evaluation:
                ideal_evaluation = xx
        #print(ideal_evaluation)
        return ideal_evaluation

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
        #print(ideal_evaluation)
        return ideal_evaluation

    def __evaluation_test(self, after_graph):
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
            if ideal_evaluation > eva:
                ideal_evaluation = eva
        #print(ideal_evaluation)
        return ideal_evaluation


    def run(self):
        self.__preprocess()
        self.__start()
        self.__process()
        self.__quit()
