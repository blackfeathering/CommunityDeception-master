import random
from similarity.jaccard import count_jaccard_index_and_recall_index
from settings import master
import logging.config
from utils.counter import count_security_index
from utils.timer import time_mark
import time
logging.config.dictConfig(master.LOGGING_SETTINGS)
logger = logging.getLogger('normal')


class RandomAnonymize(object):
    def __init__(self, graph, edges_sum, detection_func, func_args, interval, partitions=None, path=None, **kwargs):
        self.__graph = graph
        self.__edges_sum = edges_sum
        self.__detection_func = detection_func
        self.__func_args = func_args
        self.__interval = interval
        self.__partitions = partitions
        self.__path = path

        self.__edge_set = None
        self.__start_time = time.time()
        self.__end_time = None

    def __start(self):
        logger.info("=" * 60)
        logger.info("RandomAnonymize")
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
        logger.info(f'Total: {(self.__end_time - self.__start_time):10.4f} s')
        logger.info("=" * 60)
        logger.info("\n\n")

    def __preprocess(self):
        """
        预处理，把所有的边做成集合
        :return:
        """
        self.__edge_set = set(self.__graph.get_edgelist())
        if not self.__partitions:
            self.__partitions = self.__detection_func(self.__graph, **self.__func_args)
        self.__get_available_edges()

    def __get_available_edges(self):
        """
        这个方法在随机加边中废除，因为完全图的边数实在是太大了，会爆内存
        :return:
        """
        pass

    def __choose_edge(self):
        """
        随机挑选一条边，谁会那么幸运呢
        :return: tuple(source, target)
        """
        while True:
            source = random.randint(0, self.__graph.vcount() - 1)
            target = random.randint(0, self.__graph.vcount() - 1)
            if source != target:
                source, target = (source, target) if source < target else (target, source)
                # 调整顺序，保证source < target

                if (source, target) not in self.__edge_set:
                    # 确保这条边不在已有的集合中
                    return source, target

    def __should_count(self, count):
        return divmod(count, self.__interval)[1]

    def __anonymize(self):
        edges_sum = self.__edges_sum
        graph = self.__graph
        pre_partitions = self.__partitions

        counter = 1

        while counter <= edges_sum:
            edge = self.__choose_edge()
            graph.add_edge(*edge)
            security_index = 0

            if not self.__should_count(counter):
                # 判断是否需要进行划分
                fin_partitions = self.__detection_func(graph, **self.__func_args)
                modularity = self.__graph.modularity(pre_partitions.membership)
                NMI = pre_partitions.compare_to(fin_partitions, method="NMI")
                jaccard_index, recall_index = count_jaccard_index_and_recall_index(pre_partitions, fin_partitions)

                logger.info(f"{counter:<5d} jaccard index: ({jaccard_index:8.7f}), recall index: ({recall_index:8.7f}), "
                            f"security_index: ({security_index:8.7f}), modularity: ({modularity:8.7f}), NMI: ({NMI:8.7f})")

            # 把结果按一定顺序存下来，后面考虑打成log
            self.__edge_set.add(edge)
            counter += 1

    def run(self):
        self.__preprocess()
        self.__start()
        self.__anonymize()
        self.__quit()
