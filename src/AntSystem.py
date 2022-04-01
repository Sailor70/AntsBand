import random


class GraphAS(object):
    def __init__(self, cost_matrix: list, n: int, sigma: float):
        """
        :param cost_matrix: macierz kosztów przejscia - odległości między dźwiękami - większa odległość = większy koszt
        :param n: liczba węzłów grafu
        """
        self.cost_matrix = cost_matrix
        self.N = n
        self.sigma = sigma
        self.pheromone = [[self.put_pheromone(i, j) for j in range(n)] for i in range(n)]

    def put_pheromone(self, i: int, j: int):  # zainicjowanie śladu feromonowego zgodnie z oryginalną melodią
        if j == i+1:
            return self.sigma
        else:
            return 1 / (self.N * self.N)


class AntSystem(object):
    def __init__(self, ant_count: int, generations: int, alpha: float, beta: float, rho: float, q: int):
        """
        :param ant_count: liczba mrówek
        :param generations: liczba iteracji
        :param alpha: ważność feromonu
        :param beta: ważność informacji heurystycznej
        :param rho: współczynnik odparowania śladu feromonowego
        :param q: intensywność feromonu - ilość uwalnianego feromonu
        """
        self.ant_count = ant_count
        self.generations = generations
        self.alpha = alpha
        self.beta = beta
        self.rho = rho
        self.Q = q

    def solve(self, graph: GraphAS):
        best_cost = float('inf')
        best_solution = []
        for gen in range(self.generations):
            ants = [AntAS(self, graph) for i in range(self.ant_count)]
            for ant in ants:
                for i in range(graph.N - 1):
                    ant.select_next()
                if ant.total_cost < best_cost:
                    best_cost = ant.total_cost
                    best_solution = [] + ant.tabu
                ant.update_pheromone_delta()  # każda mrówka kładzie swój własny feromon po przejściu
            # print('best solution in gen #{}, cost: {}, path: {}'.format(gen, best_cost, best_solution))
            self._update_pheromone(graph, ants)
            # print('generation #{}, best cost: {}, path: {}'.format(gen, best_cost, best_solution))
        return best_solution, best_cost

    def _update_pheromone(self, graph: GraphAS, ants: list):
        for i, row in enumerate(graph.pheromone):
            for j, col in enumerate(row):
                graph.pheromone[i][j] *= 1 - self.rho
                for ant in ants:
                    graph.pheromone[i][j] += ant.pheromone_delta[i][j]


class AntAS(object):
    def __init__(self, aco: AntSystem, graph: GraphAS):
        self.colony = aco
        self.graph = graph
        self.total_cost = 0.0
        self.tabu = []  # lista tabu
        self.pheromone_delta = []  # lokalny przyrost feromonu
        self.unvisited = [i for i in range(graph.N)]  # dozwolone węzły do wyboru jako następny
        self.eta = [[0 if i == j else 1 / graph.cost_matrix[i][j] for j in range(graph.N)] for i in
                    range(graph.N)]  # informacja heurystyczna
        start = random.randint(0, graph.N - 1)  # rozpoczęcie z losowego węzła
        # start = 0  # rozpoczęcie z pierwszego - zawsze zagra oryginalną melodię
        self.tabu.append(start)
        self.current = start
        self.unvisited.remove(start)

    def select_next(self):
        denominator = 0
        for i in self.unvisited:
            denominator += self.graph.pheromone[self.current][i] ** self.colony.alpha * self.eta[self.current][
                                                                                            i] ** self.colony.beta
        probabilities = [0 for i in range(self.graph.N)]  # prawdopodobieństwa przemieszczenia się do węzła w kolejnym kroku
        for j in range(self.graph.N):
            if j in self.unvisited:
                probabilities[j] = self.graph.pheromone[self.current][j] ** self.colony.alpha * \
                                   self.eta[self.current][j] ** self.colony.beta / denominator
        # wybierz następny węzeł przez ruletkę prawdopodobieństwa
        # selected = probabilities.index(max(probabilities))  # albo wybór po prostu największego prawdopodobieństwa
        selected = 0
        rand = random.random()  # losowa liczba od 0.0 do 1.0
        for k, probability in enumerate(probabilities):
            rand -= probability
            if rand <= 0:
                selected = k  # w ten sposób wybrane zostanie potencjalnie pierwsze większę prawdopodobieństwo (niekoniecznie największe)
                break
        self.unvisited.remove(selected)
        self.tabu.append(selected)
        self.total_cost += self.graph.cost_matrix[self.current][selected]
        self.current = selected

    def update_pheromone_delta(self):
        self.pheromone_delta = [[0 for j in range(self.graph.N)] for i in range(self.graph.N)]
        for _ in range(1, len(self.tabu)):
            i = self.tabu[_ - 1]
            j = self.tabu[_]
            self.pheromone_delta[i][j] = self.colony.Q / self.total_cost
