import logging.config
import sys

from settings import master
from similarity.jaccard import count_jaccard_index_and_recall_index
from utils.counter_pre import count_security_index_by_pre
from utils.pre_counter import count_pre_security_index
from utils.timer import time_mark
import time

logging.config.dictConfig(master.LOGGING_SETTINGS)
logger = logging.getLogger('normal')


class AdvanceAnonymize(object):
    def __init__(self, graph, edges_sum, detection_func, func_args, interval, partitions=None, path=None, **kwargs):
        self.__graph = graph
        self.__edges_sum = edges_sum
        self.__detection_func = detection_func
        self.__func_args = func_args
        self.__interval = interval
        self.__partitions = partitions
        self.__path = path

        self.__available_edges = None
        self.__edge_set = None
        self.__partition_degree = None
        self.__partition_volume = None
        self.__degree_distribute = None
        self.__start_time = time.time()
        self.__end_time = None
        self.__sorted_partitions = None

    def __start(self):
        logger.info("=" * 60)
        logger.info("AdvanceAnonymize")
        logger.info(f'Time : {time_mark(self.__start_time)}')
        logger.info(f'Graph: {self.__path}')
        logger.info(f'Info : {self.__graph.vcount()} {self.__graph.ecount()}')
        logger.info(f'Edges: {self.__edges_sum}')
        logger.info(f'Func : {self.__detection_func.__name__}')
        logger.info(f'Args : {self.__func_args}')
        logger.info(f'Gap  : {self.__interval}')
        logger.info(f'Parts: {len(self.__partitions)}')
        logger.info("=" * 60)

    def __quit(self):
        self.__end_time = time.time()
        logger.info("=" * 60)
        logger.info(f'Time : {time_mark(self.__end_time)}')
        logger.info(f'Total: {(self.__end_time - self.__start_time): 10.4f} s')
        logger.info("=" * 60)
        logger.info("\n\n")

    def __preprocess(self):
        self.__edge_set = set(self.__graph.get_edgelist())
        if not self.__partitions:
            self.__partitions = self.__detection_func(self.__graph, **self.__func_args)
        self.__set_necessary_info()

    def __set_necessary_info(self):
        partition_degree = list()
        partition_volume = list()
        sorted_partitions = list()

        partitions = self.__partitions
        for index, part in enumerate(partitions):
            subgraph = self.__partitions.subgraph(index)
            partition_degree.append(2 * subgraph.ecount())
            partition_volume.append(sum(self.__graph.degree(part)))
            sorted_partitions.append(sorted(part, key=lambda x: self.__graph.degree(x)))

        # 这地方有个bug, self.__graph.degree(subgraph.vs)可能会返回所有的节点的值
        # 好吧，好像不是bug，是它自己没做类型检查，对于不认识的类型，一律返回全部节点

        self.__partition_degree = partition_degree
        self.__partition_volume = partition_volume
        self.__degree_distribute = self.__graph.degree(self.__graph.vs)
        self.__sorted_partitions = sorted_partitions

    def __get_available_edges(self):
        min_degree_node_list = list()

        for partition in self.__partitions:
            min_degree_node_list.append(min(partition, key=lambda x: self.__graph.degree(x)))

        # 检查有没有足够的边用来加
        subgraph = self.__graph.subgraph(min_degree_node_list)
        max_edges = subgraph.vcount() * (subgraph.vcount() - 1) / 2
        if subgraph.ecount() >= max_edges:
            raise ValueError("Not enough edges to add.")

        # 之前拿到的节点做一次排序，为了保证产生的边的顺序
        min_degree_node_list.sort()
        available_edges = set()

        # 遍历这些节点，从里面产生需要的边
        for source in range(len(min_degree_node_list)):
            for target in range(source + 1, len(min_degree_node_list)):
                edge = (min_degree_node_list[source], min_degree_node_list[target])
                if edge not in self.__edge_set:
                    available_edges.add(edge)

        self.__available_edges = available_edges

    def __get_available_edges_pro(self):
        partitions = self.__sorted_partitions
        available_edges = set()

        for a_part in partitions:
            for b_part in partitions:
                a_degree, b_degree = self.__graph.degree(a_part[0]), self.__graph.degree(b_part[0])
                min_degree = a_degree if a_degree < b_degree else b_degree

                # find max_degree
                max_degree = 0
                flag = False
                for a_vertex in a_part:
                    if flag:
                        break
                    for b_vertex in b_part:
                        if a_vertex == b_vertex:
                            continue

                        # make sure the vertex's order is desc
                        edge = (a_vertex, b_vertex) if a_vertex < b_vertex else (b_vertex, a_vertex)

                        if edge not in self.__edge_set:
                            max_degree = self.__graph.degree(a_vertex) + self.__graph.degree(b_vertex)
                            flag = True
                            break

                for a_vertex in a_part:
                    if self.__graph.degree(a_vertex) > max_degree - min_degree:
                        break

                    for b_vertex in b_part:
                        sum_degree = self.__graph.degree(a_vertex) + self.__graph.degree(b_vertex)
                        if sum_degree <= max_degree:
                            edge = (a_vertex, b_vertex) if a_vertex < b_vertex else (b_vertex, a_vertex)
                            if edge not in self.__edge_set:
                                available_edges.add(edge)
                        else:
                            break

            self.__available_edges = available_edges

    def __choose_edge(self):
        self.__get_available_edges_pro()
        # 取当前可用的边

        # 把后续函数需要调用的数据先取出来
        partitions = self.__partitions
        add_edge = None
        chosen_partition_module = None
        min_security = sys.maxsize
        total_degree = 2 * self.__graph.ecount()
        degree_distribute = self.__degree_distribute
        membership = partitions.membership
        # 时间优化的一个关键点，容易遗漏，即在python的对象引用中，是需要一定时间开销的

        # 预先计算出一部分值，在循环中避免多次计算
        pre_count = count_pre_security_index(self.__graph, partitions, self.__partition_degree, self.__partition_volume)

        for edge in self.__available_edges:
            src_des = (membership[edge[0]], membership[edge[1]])
            security_index = count_security_index_by_pre(pre_count, edge, src_des, total_degree + 2,
                                                         self.__partition_degree, self.__partition_volume,
                                                         degree_distribute)

            if security_index < min_security:
                min_security = security_index
                add_edge = edge
                chosen_partition_module = src_des

        self.__graph.add_edge(*add_edge)
        self.__edge_set.add(add_edge)
        self.__partition_volume[chosen_partition_module[0]] += 1
        self.__partition_volume[chosen_partition_module[1]] += 1
        self.__degree_distribute[add_edge[0]] += 1
        self.__degree_distribute[add_edge[1]] += 1

        self.__sorted_partitions[chosen_partition_module[0]].sort(key=lambda x: self.__graph.degree(x))
        self.__sorted_partitions[chosen_partition_module[1]].sort(key=lambda x: self.__graph.degree(x))

        return min_security

    def __should_count(self, count):
        return divmod(count, self.__interval)[1]

    def __anonymize(self):
        edge_sum = self.__edges_sum
        pre_partitions = self.__partitions
        count = 1

        while count <= edge_sum:
            try:
                security_index = self.__choose_edge()
            except ValueError:
                logger.info(f'{count:<5d} Not enough edges to add.')
                return -1

            if not self.__should_count(count):
                fin_partitions = self.__detection_func(self.__graph, **self.__func_args)

                jaccard_index, recall_index = count_jaccard_index_and_recall_index(pre_partitions, fin_partitions)
                modularity = self.__graph.modularity(pre_partitions.membership)
                NMI = pre_partitions.compare_to(fin_partitions, method="NMI")

                logger.info(f"{count:<5d} jaccard index: ({jaccard_index:8.7f}), recall index: ({recall_index:8.7f}), "
                            f"security_index: ({security_index:8.7f}), modularity: ({modularity:8.7f}), NMI: ({NMI:8.7f})")

            count += 1

    def run(self):
        self.__preprocess()
        self.__start()
        self.__anonymize()
        self.__quit()
