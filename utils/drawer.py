import matplotlib.pyplot as plt
from utils.log_extractor import LogExtractor


class Drawer(object):
    def __init__(self, t, x):
        plt.ylabel('Index')
        plt.xlabel('Number of Added Edges ')
        plt.title(t)
        self.__x = x
        return

    def setx(self, li):
        plt.xticks(self.__x, li, rotation=0)
        return

    def add(self, y, title='title', col='r', point='o'):
        plt.plot(self.__x, y, label=title, linewidth=2, color=col, marker=point, markerfacecolor=col, markersize=12)

    @staticmethod
    def show():
        plt.legend()
        plt.show()


if __name__ == '__main__':
    size = 5  # 平均间隔

    log_extractor = LogExtractor('../logs/jazz_infomap_1000_10_30.log')
    y1 = log_extractor.get_average("Advance")['jaccard']
    y2 = log_extractor.get_average("Random")['jaccard']

    y1 = [sum(y1[i: i + size]) / size for i in range(0, len(y1), size)]
    y2 = [sum(y2[i: i + size]) / size for i in range(0, len(y2), size)]

    x = [i for i in range(len(y1))]

    d = Drawer('jaccard', x)

    d.setx(x)
    d.add(y1, 'aaa', 'r', 'o')
    d.add(y2, 'bbb', 'g', '^')
    # d.add(y3, 'ccc', 'b', 'v')
    # d.add(y4, 'ddd', 'pink', '+')
    # d.add(y5, 'eee', 'black', 'x')

    plt.text(0, 0.4, 'boxedjkjk', bbox={'facecolor': 'grey', 'alpha': 0.2, 'pad': 8})

    d.show()
