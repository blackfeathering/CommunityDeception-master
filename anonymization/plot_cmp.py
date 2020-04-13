import matplotlib.pyplot as plt
from settings import master


def plot_cmp(fastadd=0, radomadd=0, mindegreeadd=0, betweenessadd=0, maxdegreeadd=0, ctrperadd=0, num=master.GRAPH_SETTINGS['edges_sum']):
    x_data = list()
    if num < 100:
        x_data = [i for i in range(0, num + 1)]
    elif 100 <= num < 1000:
        for i in range(0, num + 1):
            if i % 10 == 0:
                x_data.append(i)
    elif num >= 1000:
        for i in range(0, num + 1):
            if i % 100 == 0:
                x_data.append(i)

    if fastadd != 0:
        fname = master.GRAPH_SETTINGS['path'][8:len(master.GRAPH_SETTINGS['path'])]
        with open('test/{}_{}_{}_evaluation.txt'.format(fname, master.GRAPH_SETTINGS['edges_sum'], 'fastadd'),
                  'r') as f:
            list1 = f.readlines()
        y0_data = list()
        for line in list1:
            y0_data.append(float(line))
        plt.plot(x_data, y0_data, c='r', label='fastadd')

    if radomadd != 0:
        fname = master.GRAPH_SETTINGS['path'][8:len(master.GRAPH_SETTINGS['path'])]
        with open('test/{}_{}_{}_evaluation.txt'.format(fname, master.GRAPH_SETTINGS['edges_sum'], 'radomadd'),
                  'r') as f:
            list1 = f.readlines()
        y1_data = list()
        for line in list1:
            y1_data.append(float(line))
        plt.plot(x_data, y1_data, c='b', label='radomadd')

    if mindegreeadd != 0:
        fname = master.GRAPH_SETTINGS['path'][8:len(master.GRAPH_SETTINGS['path'])]
        with open('test/{}_{}_{}_evaluation.txt'.format(fname, master.GRAPH_SETTINGS['edges_sum'], 'mindegreeadd'),
                  'r') as f:
            list1 = f.readlines()
        y2_data = list()
        for line in list1:
            y2_data.append(float(line))
        plt.plot(x_data, y2_data, c='g', label='mindegreeadd')

    if betweenessadd != 0:
        fname = master.GRAPH_SETTINGS['path'][8:len(master.GRAPH_SETTINGS['path'])]
        with open('test/{}_{}_{}_evaluation.txt'.format(fname, master.GRAPH_SETTINGS['edges_sum'], 'betweenessadd'),
                  'r') as f:
            list1 = f.readlines()
        y3_data = list()
        for line in list1:
            y3_data.append(float(line))
        plt.plot(x_data, y3_data, c='y', label='betweenessadd')

    if maxdegreeadd != 0:
        fname = master.GRAPH_SETTINGS['path'][8:len(master.GRAPH_SETTINGS['path'])]
        with open('test/{}_{}_{}_evaluation.txt'.format(fname, master.GRAPH_SETTINGS['edges_sum'], 'maxdegreeadd'),
                  'r') as f:
            list1 = f.readlines()
        y3_data = list()
        for line in list1:
            y3_data.append(float(line))
        plt.plot(x_data, y3_data, c='k', label='maxdegreeadd')

    if ctrperadd != 0:
        fname = master.GRAPH_SETTINGS['path'][8:len(master.GRAPH_SETTINGS['path'])]
        with open('test/{}_{}_{}_evaluation.txt'.format(fname, master.GRAPH_SETTINGS['edges_sum'], 'ctrperadd'),
                  'r') as f:
            list1 = f.readlines()
        y3_data = list()
        for line in list1:
            y3_data.append(float(line))
        plt.plot(x_data, y3_data, c='k', label='ctrperadd')

    plt.xlabel('add edge num')
    plt.ylabel('combine degree')
    plt.legend()
    plt.title('{} community combine'.format(fname))
    plt.show()
