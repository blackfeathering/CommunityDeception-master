import logging.config
import random
import sys
import time
from operator import itemgetter
from typing import List
import pickle

from igraph import Graph
from igraph.clustering import VertexClustering

from settings import master
from utils.counter import count_security_index_inside
from utils.timer import time_mark
import os
from utils.partitionIO import load_partition

logging.config.dictConfig(master.LOGGING_SETTINGS)
logger = logging.getLogger('console')


class SIPAnonymize(object):
    def __init__(self, edges_sum, detection_func, func_args, interval, parts_path, source_community_index, edges_path, **kwargs):
        self.__parts: VertexClustering = load_partition(parts_path)
        self.__graph: Graph = self.__parts.graph
        self.__edges_sum = edges_sum
        self.__detection_func = detection_func
        self.__func_args = func_args
        self.__interval = interval
        self.__src_com_index = source_community_index
        self.__graph_name = os.path.splitext(os.path.basename(parts_path))[0]

        self.__degrees: List[int] = self.__graph.degree(self.__graph.vs)
        self.__membership = self.__parts.membership
        self.__min_nodes = dict()
        self.__max_pairs = dict()
        self.__src_com_nodes = set(self.__parts[self.__src_com_index])
        self.__edges_file = open(edges_path, "wb")
        self.__add_edges = list()

        self.__start_time = time.time()
        self.__end_time = None

    def __start(self):
        logger.info("=" * 60)
        logger.info("SIPAnonymize")
        logger.info(f'Time : {time_mark(self.__start_time)}')
        logger.info(f'Graph: {self.__graph_name}')
        logger.info(f'Info : {self.__graph.vcount()} {self.__graph.ecount()}')
        logger.info(f'Edges: {self.__edges_sum}')
        logger.info(f'TCI: {self.__src_com_index}')
        logger.info(f'Func : {self.__detection_func.__name__}')
        logger.info(f'Args : {self.__func_args}')
        logger.info(f'Gap  : {self.__interval}')
        logger.info(f'Parts: {len(self.__parts)}')
        logger.info(f'TCI Size: {len(self.__src_com_nodes)}')
        logger.info("=" * 60)

    def __quit(self):
        pickle.dump(self.__add_edges, self.__edges_file)
        self.__edges_file.close()

        self.__end_time = time.time()
        logger.info("=" * 60)
        logger.info(f'Time : {time_mark(self.__end_time)}')
        logger.info(f'Total: {(self.__end_time - self.__start_time):10.4f} s')
        logger.info("=" * 60)
        logger.info("\n\n")

    def __preprocess(self):
        for index in range(len(self.__parts)):
            self.__update_min_nodes(index)

        for node in self.__parts[self.__src_com_index]:
            self.__update_max_pairs(node)

    def __edge_exist(self, edge):
        return self.__graph.get_eid(*edge, directed=False, error=False) != -1

    def __get_neighbors_within_src(self, node):
        """
        返回这个点在src社区内的所有邻居，以生成器的形式返回。
        :param node:
        :return:
        """
        for neighbor in self.__graph.neighbors(node):
            if neighbor not in self.__src_com_nodes:
                continue
            yield neighbor

    def __update_max_pairs(self, node):
        """
        找到给定点在社区内部的邻居中，有最大度的那个，并更新max_pairs，如果这个点在社区中没有邻居，那么在max_pairs中删除这个键值
        :param node:
        :return:
        """

        max_neighbor, max_degree = -1, -1
        for neighbor in self.__get_neighbors_within_src(node):
            if self.__degrees[neighbor] > max_degree:
                max_neighbor, max_degree = neighbor, self.__degrees[neighbor]

        if max_degree == -1:
            if node in self.__max_pairs:
                del self.__max_pairs[node]
        elif node in self.__src_com_nodes:
            self.__max_pairs[node] = max_neighbor

    def __update_min_nodes(self, part_index):
        """
        记录每个社区中的最小度，并更新到min_nodes中
        :param part_index:
        :return:
        """
        min_node, min_degree = -1, sys.maxsize

        if part_index == self.__src_com_index:
            self.__min_nodes[part_index] = min(self.__parts[part_index], key=lambda x: self.__degrees[x])
            return

        for node in self.__parts[part_index]:
            if self.__degrees[node] < min_degree:
                min_node, min_degree = node, self.__degrees[node]

        self.__min_nodes[part_index] = min_node

    def __get_add_edge(self) -> (int, int, float):
        parts_indices = [index for index in range(len(self.__parts)) if index != self.__src_com_index]
        random.shuffle(parts_indices)

        u, v, min_degree = self.__min_nodes[self.__src_com_index], -1, sys.maxsize
        for node in itemgetter(*parts_indices)(self.__min_nodes):
            if self.__degrees[node] < min_degree and not self.__edge_exist((node, u)):
                v, min_degree = node, self.__degrees[node]

        self.__graph.add_edge(u, v)
        result = u, v, count_security_index_inside(self.__graph, self.__src_com_index, self.__parts)
        self.__graph.delete_edges([(u, v), ])
        return result

    def __get_del_edge(self) -> (int, int, float):
        u_min, v_min = -1, -1
        max_degree_sum, min_degree = 0, sys.maxsize
        min_security_index = 2
        degrees = self.__degrees

        for u, v in self.__max_pairs.items():
            if degrees[u] + degrees[v] <= max_degree_sum and min(degrees[u], degrees[v]) < min_degree:
                continue

            self.__graph.delete_edges([(u, v), ])
            security_index = count_security_index_inside(self.__graph, self.__src_com_index, self.__parts)
            self.__graph.add_edge(u, v)

            if security_index < min_security_index:
                u_min, v_min = u, v
                min_security_index = security_index
                max_degree_sum, min_degree = degrees[u] + degrees[v], min(degrees[u], degrees[v])

        return u_min, v_min, min_security_index

    def __choose_edge(self):
        *add_edge, add_security_index = self.__get_add_edge()
        *del_edge, del_security_index = self.__get_del_edge()

        if add_security_index <= del_security_index:
            return True, add_edge, add_security_index
        else:
            return False, del_edge, del_security_index

    def __should_count(self, count):
        return not divmod(count, self.__interval)[1]

    def __anonymize(self):
        edge_sum = self.__edges_sum
        count = 1

        while count <= edge_sum:
            flag, edge, security_index = self.__choose_edge()

            self.__round_update(flag, edge, )

            if self.__should_count(count):
                logger.info(f"Processing: {count}/{self.__edges_sum}")

            self.__add_edges.append((edge, flag, security_index))
            self.__graph.betweenness()
            count += 1

    def __round_update(self, flag, edge):
        src, tar = edge

        if flag:
            self.__graph.add_edge(*edge)
            self.__degrees[src] += 1
            self.__degrees[tar] += 1

        else:
            self.__graph.delete_edges([tuple(edge), ])
            self.__degrees[src] -= 1
            self.__degrees[tar] -= 1

        self.__round_update_min_nodes(flag, edge)
        self.__round_update_max_pairs(flag, edge)

    def __round_update_min_nodes(self, flag, edge):
        if not flag:
            return

        for index in itemgetter(*edge)(self.__membership):
            self.__update_min_nodes(index)

    def __round_update_max_pairs(self, flag, edge):
        degrees = self.__degrees

        for update_node in edge:
            if update_node not in self.__src_com_nodes:
                continue

            for node in self.__get_neighbors_within_src(update_node):
                if degrees[self.__max_pairs[node]] >= degrees[update_node]:
                    continue

                self.__max_pairs[node] = update_node

        else:
            for update_node in edge:
                self.__update_max_pairs(update_node)

                if update_node not in self.__max_pairs:
                    continue

                for node in self.__get_neighbors_within_src(update_node):
                    if node not in self.__max_pairs or self.__max_pairs[node] != update_node:
                        continue

                    self.__update_max_pairs(node)

    def run(self):
        self.__preprocess()
        self.__start()
        self.__anonymize()
        self.__quit()