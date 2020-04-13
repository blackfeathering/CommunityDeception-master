import logging.config
from typing import List
from settings import master
from igraph import Graph
import random
from igraph.clustering import VertexClustering
from math import log
from utils.timer import time_mark
import time

logging.config.dictConfig(master.LOGGING_SETTINGS)
logger = logging.getLogger('normal')


class CommunityCombine(object):
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

    def __pre_securiy_index_cul(self, vertex_list, edge_list, graph):
        g = 0
        for edge in edge_list:
            if edge[0] in vertex_list and edge[1] not in vertex_list:
                g += 1
            if edge[1] in vertex_list and edge[0] not in vertex_list:
                g += 1

        var = 0
        for i in vertex_list:
            var += graph.vs[i].degree()

        total_degree = 2 * graph.ecount()
        return (g, total_degree, var)

    def __count_security_index(self, g, total_degree, var, graph, vertex_list0, vertex_list1):
        position_entropy = 0
        for i in vertex_list0:
            d = i[0] / total_degree
            position_entropy += d * log(d, 2)
        for i in vertex_list1:
            d = i[0] / total_degree
            position_entropy += d * log(d, 2)

        resistance = (var - g) / total_degree * log(var / total_degree, 2)

        security_index = resistance / position_entropy
        return security_index

    def __combine(self):
        Max_vertex0 = self.__vertex_list[self.__degree_list.index(max(self.__degree_list))]
        Max_part0 = self.__vertex_part[self.__vertex_list.index(Max_vertex0)]
        vertex_part1 = Max_part0 ^ 1
        vertex_list0 = list()  # ((degree,index))
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

        # fast算法需要的参数
        cross_edge_list = list()  # 两个社区之间的边
        for edge in self.__edge_set:
            if edge[0] in self.__vertex_list and edge[1] in self.__vertex_list:
                cross_edge_list.append(edge)
            if edge[0] in self.__vertex_list and edge[1] in self.__vertex_list:
                cross_edge_list.append(edge)
        updater_edge = list()   # 用于更新记录对面没链接的最大度的点(vertex1,vertex0,count列表的搜索位置)
        for vertex in self.__vertex_list:
            for index0 in range(len(vertex_list0)):
                if vertex == vertex_list0[index0][1]:
                    for i in range(len(vertex_list1)):
                        if (vertex, vertex_list1[i][1]) not in cross_edge_list and (vertex_list1[i][1], vertex) not in cross_edge_list:
                            updater_edge.append((vertex, vertex_list1[i][1], i))
                            break
                    break
            for index1 in range(len(vertex_list1)):
                if vertex == vertex_list1[index1][1]:
                    for i in range(len(vertex_list0)):
                        if (vertex, vertex_list0[i][1]) not in cross_edge_list and (vertex_list0[i][1], vertex) not in cross_edge_list:
                            updater_edge.append((vertex, vertex_list0[i][1], i))
                            break
                    break


        fname = master.GRAPH_SETTINGS['path'][8:len(master.GRAPH_SETTINGS['path'])]
        f = open('test/{}_{}_fastadd.txt'.format(fname, master.GRAPH_SETTINGS['edges_sum']), 'w')


        canshu = self.__pre_securiy_index_cul(self.__vertex_list, after_graph.get_edgelist(), after_graph)
        g = canshu[0]
        total_degree = canshu[1]
        var = canshu[2]
        '''
        ideal_evaluation = 0
        for i in range(0, 9):
            ideal_evaluation += self.__evaluation(after_graph)
        ideal_evaluation /= 10
        logger.info(f"evaluation: ({ideal_evaluation:8.7f})")
        logger.info("=" * 10)
        '''
        for i in range(0, self.__edges_sum):

            #edgeadd = self.__enum_add_edge(vertex_list0, vertex_list1, after_graph, self.__vertex_list,
             #                              g, total_degree, var)
            '''
            ss = '('+str(edgeadd0[0])+','+str(edgeadd0[1])+')'+'\n'
            f.write(ss)
            '''

            edgeadd = self.__fast_add_edge(vertex_list0, vertex_list1, updater_edge, after_graph, g, total_degree, var)

            if edgeadd not in self.__edge_set:
                after_graph.add_edge(edgeadd[0], edgeadd[1])
                self.__edge_set.add(edgeadd)
                cross_edge_list.append(edgeadd)
                updater_edge = self.__update(updater_edge, cross_edge_list, vertex_list0, vertex_list1, edgeadd)

                s = '('+str(edgeadd[0])+','+str(edgeadd[1])+')'+'\n'
                f.write(s)
                total_degree += 2
                var += 2
                for index in range(len(vertex_list0)):
                    if vertex_list0[index][1] == edgeadd[0] or vertex_list0[index][1] == edgeadd[1]:
                        vertex_list0[index] = (vertex_list0[index][0] + 1, vertex_list0[index][1])
                        break
                for index in range(len(vertex_list1)):
                    if vertex_list1[index][1] == edgeadd[0] or vertex_list1[index][1] == edgeadd[1]:
                        vertex_list1[index] = (vertex_list1[index][0] + 1, vertex_list1[index][1])
                        break
                vertex_list0.sort(reverse=True, key=lambda x: x[0])
                vertex_list1.sort(reverse=True, key=lambda x: x[0])
            '''
            if i % 10 == 0:
                ideal_evaluation = 0
                for ii in range(0, 10):
                    ideal_evaluation += self.__evaluation(after_graph)
                ideal_evaluation /= 10
                logger.info(f"evaluation: ({ideal_evaluation:8.7f})")
                logger.info("=" * 10)
            '''

        f.close()

    def __enum_add_edge(self, vertex_list0, vertex_list1, graph, vertex_list, g, total_degree, var):
        Max_scurty = 0
        #testg = graph.copy()
        for i in vertex_list0:
            for j in vertex_list1:
                if (i[1], j[1]) not in self.__edge_set and (j[1], i[1]) not in self.__edge_set:
                    edge_add = (i[1], j[1])
                    i0 = 0
                    i1 = 0
                    for index in range(len(vertex_list0)):
                        if vertex_list0[index][1] == edge_add[0] or vertex_list0[index][1] == edge_add[1]:
                            i0 = index
                            vertex_list0[index] = (vertex_list0[index][0] + 1, vertex_list0[index][1])
                            break
                    for index in range(len(vertex_list1)):
                        if vertex_list1[index][1] == edge_add[0] or vertex_list1[index][1] == edge_add[1]:
                            i1 = index
                            vertex_list1[index] = (vertex_list1[index][0] + 1, vertex_list1[index][1])
                            break
                    xx = self.__count_security_index(g, total_degree + 2, var + 2, graph, vertex_list0, vertex_list1)
                    vertex_list0[i0] = (vertex_list0[i0][0] - 1, vertex_list0[i0][1])
                    vertex_list1[i1] = (vertex_list1[i1][0] - 1, vertex_list1[i1][1])
                    vertex_list0.sort(reverse=True, key=lambda x: x[0])
                    vertex_list1.sort(reverse=True, key=lambda x: x[0])
                    if xx > Max_scurty:
                        Max_scurty = xx
                        v0 = (i[0], i[1])
                        v1 = (j[0], j[1])
                        edgeadd = (i[1], j[1])

        logger.info(f"edge added: {v0[1], v1[1]}, dergee: {v0[0], v1[0]}, security index: ({Max_scurty:8.7f}),")

        return edgeadd

    def __random_add_edge(self, vertex_list0, vertex_list1):
        while True:
            a = random.randint(0, len(vertex_list0))
            b = random.randint(0, len(vertex_list1))
            if (vertex_list0[a], vertex_list1[b]) not in self.__edge_set and (vertex_list1[b], vertex_list0[a]) not in self.__edge_set:
                edgeadd = (vertex_list0[a], vertex_list1[b])
                return edgeadd

    def __fast_add_edge(self, vertex_list0, vertex_list1, updater_edge, graph, g, total_degree, var):
        Max_scurty = 0
        edgeadd = (0, 0)
        for item in updater_edge:
            edge = (item[0], item[1])
            #graph.add_edge(edge[0], edge[1])
            i0 = 0
            i1 = 0
            for index in range(len(vertex_list0)):
                if vertex_list0[index][1] == item[0] or vertex_list0[index][1] == item[1]:
                    i0 = index
                    vertex_list0[index] = (vertex_list0[index][0] + 1, vertex_list0[index][1])
                    break
            for index in range(len(vertex_list1)):
                if vertex_list1[index][1] == item[0] or vertex_list1[index][1] == item[1]:
                    i1 = index
                    vertex_list1[index] = (vertex_list1[index][0] + 1, vertex_list1[index][1])
                    break
            xx = self.__count_security_index(g, total_degree + 2, var + 2, graph, vertex_list0, vertex_list1)
            vertex_list0[i0] = (vertex_list0[i0][0] - 1, vertex_list0[i0][1])
            vertex_list1[i1] = (vertex_list1[i1][0] - 1, vertex_list1[i1][1])
            #graph.delete_edges(edge)
            if xx > Max_scurty:
                Max_scurty = xx
                edgeadd = edge
                v0 = (vertex_list0[i0][0], vertex_list0[i0][1])
                v1 = (vertex_list1[i1][0], vertex_list1[i1][1])

        logger.info(f"edge added: {v0[1], v1[1]}, dergee: {v0[0], v1[0]}, security index: ({Max_scurty:8.7f}),")

        return edgeadd

    def __update(self, updater_edge, cross_edge_list, vertex_list0, vertex_list1, edgeadd):
        for index in range(len(updater_edge)):
            if (updater_edge[index][0], updater_edge[index][1]) == edgeadd or (updater_edge[index][1], updater_edge[index][0]) == edgeadd:
                for i in range(len(vertex_list0)):
                    if vertex_list0[i][1] == updater_edge[index][0]:
                        for j in range(0, len(vertex_list1)):
                            if (updater_edge[index][0], vertex_list1[j][1]) not in cross_edge_list and (vertex_list1[j][1], updater_edge[index][0]) not in cross_edge_list:
                                updater_edge[index] = (updater_edge[index][0], vertex_list1[j][1], j)
                                break
                        break
                for i in range(len(vertex_list1)):
                    if vertex_list1[i][1] == updater_edge[index][0]:
                        for j in range(0, len(vertex_list0)):
                            if (updater_edge[index][0], vertex_list0[j][1]) not in cross_edge_list and (vertex_list0[j][1], updater_edge[index][0]) not in cross_edge_list:
                                updater_edge[index] = (updater_edge[index][0], vertex_list0[j][1], j)
                                break
                        break


        return updater_edge

    '''
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
        return ideal_evaluation
    '''
    def run(self):
        self.__preprocess()
        self.__start()
        self.__combine()
        self.__quit()
