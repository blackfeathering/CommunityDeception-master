import os

from utils.log_extractor import LogExtractor

log_dir = 'logs'
log_name_list = os.listdir(log_dir)
result = dict()

for log_name in log_name_list:
    _, add_edges, interval, generation = log_name.rstrip('.log').rsplit('_', maxsplit=3)
    graph_name, func = _.rsplit('_', maxsplit=1)

    log_extractor = LogExtractor(os.path.join(log_dir, log_name))

    def quick_func(log_temp, property):
        temp = log_temp.get(property, [0])[-10:]
        return round(sum(temp) / len(temp), 6)

    random = log_extractor.get_average('Random')
    random_jaccard = quick_func(random, 'jaccard')
    random_nmi = quick_func(random, 'nmi')
    random_recall = quick_func(random, 'recall')
    random_security = quick_func(random, 'security')
    random_modularity = quick_func(random, 'modularity')

    normal = log_extractor.get_average('Normal')
    normal_jaccard = quick_func(normal, 'jaccard')
    normal_nmi = quick_func(normal, 'nmi')
    normal_recall = quick_func(normal, 'recall')
    normal_security = quick_func(normal, 'security')
    normal_modularity = quick_func(normal, 'modularity')

    advance = log_extractor.get_average('Advance')
    advance_jaccard = quick_func(advance, 'jaccard')
    advance_nmi = quick_func(advance, 'nmi')
    advance_recall = quick_func(advance, 'recall')
    advance_security = quick_func(advance, 'security')
    advance_modularity = quick_func(advance, 'modularity')

    print(
        f'''
        Graph name: {graph_name}
        Func  name: {func}
        Add edges : {add_edges}
        Result    : 
            Jaccard:
                Random : {random_jaccard}
                Normal : {normal_jaccard}
                Advance: {advance_jaccard}
            Recall:
                Random : {random_recall}
                Normal : {normal_recall}
                Advance: {advance_recall}
            NMI:
                Random : {random_nmi}
                Normal : {normal_nmi}
                Advance: {advance_nmi}
            Security:
                Random : {random_security}
                Normal : {normal_security}
                Advance: {advance_security}
            Modularity:
                Random : {random_modularity}
                Normal : {normal_modularity}
                Advance: {advance_modularity}
        '''
    )
