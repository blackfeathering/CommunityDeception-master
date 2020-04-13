from igraph import Graph
from anonymization.communitty_combine_new import CommunityCombine
from anonymization.community_evaluation import CommunityEvaluation
from anonymization.radon_combine import RadomCombine
from anonymization.Mindegree_combine import MindegreeCombine
from anonymization.betweeness_combine import BetweenessCombine
from anonymization.maxdegree_test import maxdegreeCombine
from anonymization.ctrper import ctrperCombine
from anonymization.plot_cmp import plot_cmp
from settings import master
import logging.config

logging.config.dictConfig(master.LOGGING_SETTINGS)
logger = logging.getLogger('normal')

def choose_partitions(graph, times=10):
    max_modularity = 0
    max_partitions = None

    while times:
        temp_partitions = master.GRAPH_SETTINGS['detection_func'](graph, **master.GRAPH_SETTINGS['func_args'])
        modularity = temp_partitions.modularity
        if max_modularity < modularity:
            max_modularity = modularity
            max_partitions = temp_partitions

        times -= 1

    return max_partitions


if __name__ == '__main__':
    test_graph = Graph.Read_GML(master.GRAPH_SETTINGS['path'])
    partitions = choose_partitions(test_graph)

    # for part in partitions:
    #    logger.info(f'{part}')
    # test_graph.write_gml('test/before.gml')
    # print(test_graph.get_edgelist())
    i0 = 1
    i1 = 2
    #############################################################
    #fastadd    radomadd      mindegreeadd     betweenessadd    maxdegreeadd
    combine = CommunityCombine(graph=test_graph.copy(), partitions=partitions, index0=i0, index1=i1, **master.GRAPH_SETTINGS)
    combine.run()
    eval = CommunityEvaluation(graph=test_graph.copy(), partitions=partitions, index0=i0, index1=i1, ffname='fastadd',
                               **master.GRAPH_SETTINGS)
    eval.run()

    cmp1 = RadomCombine(graph=test_graph.copy(), partitions=partitions, index0=i0, index1=i1, **master.GRAPH_SETTINGS)
    #cmp1.run()
    eval1 = CommunityEvaluation(graph=test_graph.copy(), partitions=partitions, index0=i0, index1=i1, ffname='radomadd',  **master.GRAPH_SETTINGS)
    #eval1.run()

    cmp2 =MindegreeCombine(graph=test_graph.copy(), partitions=partitions, index0=i0, index1=i1, **master.GRAPH_SETTINGS)
    cmp2.run()
    eval2 = CommunityEvaluation(graph=test_graph.copy(), partitions=partitions, index0=i0, index1=i1, ffname='mindegreeadd', **master.GRAPH_SETTINGS)
    eval2.run()

    cmp3 = BetweenessCombine(graph=test_graph.copy(), partitions=partitions, index0=i0, index1=i1, **master.GRAPH_SETTINGS)
    #cmp3.run()
    eval3 = CommunityEvaluation(graph=test_graph.copy(), partitions=partitions, index0=i0, index1=i1, ffname='betweenessadd', **master.GRAPH_SETTINGS)
    #eval3.run()

    cmp4 = maxdegreeCombine(graph=test_graph.copy(), partitions=partitions, index0=i0, index1=i1, **master.GRAPH_SETTINGS)
    #cmp4.run()
    eval4 = CommunityEvaluation(graph=test_graph.copy(), partitions=partitions, index0=i0, index1=i1, ffname='maxdegreeadd', **master.GRAPH_SETTINGS)
    #eval4.run()

    cmp5 = ctrperCombine(graph=test_graph.copy(), partitions=partitions, index0=i0, index1=i1, **master.GRAPH_SETTINGS)
    cmp5.run()
    eval5 = CommunityEvaluation(graph=test_graph.copy(), partitions=partitions, index0=i0, index1=i1,
                               ffname='ctrperadd', **master.GRAPH_SETTINGS)
    eval5.run()

    plot_cmp(fastadd=1, radomadd=0, mindegreeadd=1, betweenessadd=0, maxdegreeadd=0, ctrperadd=1)
    # advance = AdvanceAnonymize(graph=test_graph.copy(), partitions=partitions, **master.GRAPH_SETTINGS)
    # advance.run()
    # ulti = UltimateAnonymize(graph=test_graph.copy(), partitions=partitions, **master.GRAPH_SETTINGS)
    # ulti.run()
