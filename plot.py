import matplotlib.pyplot as plt


def plot(points, path: list):
    x = []
    y = []
    print(points)
    for i in range(len(points)):
        x.append(i)
        y.append(points[path[i]])

    plt.plot(x, y, 'co')
    plt.show()
