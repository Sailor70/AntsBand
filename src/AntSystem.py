import random

class GraphAS(object):
    def __init__(self, cost_matrix: list, rank: int, sigma: float):
        """
        :param cost_matrix: macierz kosztów przejscia - odległości między dźwiękami - większa odległość = większy koszt
        :param rank: liczba węzłów grafu
        """
        self.matrix = cost_matrix
        self.rank = rank
        self.sigma = sigma
        self.pheromone = [[self.put_pheromone(i, j) for j in range(rank)] for i in range(rank)]

    def put_pheromone(self, i: int, j: int):  # zainicjowanie śladu feromonowego zgodnie z oryginalną melodią
        if j == i+1:
            return self.sigma
        else:
            return 1 / (self.rank * self.rank)


class ACO(object):
    def __init__(self, ant_count: int, generations: int, alpha: float, beta: float, rho: float, q: int):
        """
        :param ant_count: liczba mrówek
        :param generations: liczba iteracji
        :param alpha: ważność feromonu
        :param beta: ważność informacji heurystycznej
        :param rho: współczynnik odparowania śladu feromonowego
        :param q: intensywność feromonu - ilość uwalnianego feromonu
        """
        self.Q = q
        self.rho = rho
        self.beta = beta
        self.alpha = alpha
        self.ant_count = ant_count
        self.generations = generations
        # self.divider = 1  #  eksperymentalnie - do tworzenia krótkich, powtarzalnych melodii

    def _update_pheromone(self, graph: GraphAS, ants: list):
        for i, row in enumerate(graph.pheromone):
            for j, col in enumerate(row):
                graph.pheromone[i][j] *= 1 - self.rho  # 1-self.rho
                for ant in ants:
                    graph.pheromone[i][j] += ant.pheromone_delta[i][j]

    # noinspection PyProtectedMember
    def solve(self, graph: GraphAS):
        """
        :param graph:
        """
        best_cost = float('inf')
        best_solution = []
        for gen in range(self.generations):
            # noinspection PyUnusedLocal
            ants = [_Ant(self, graph) for i in range(self.ant_count)]
            for ant in ants:
                for i in range(graph.rank - 1):
                    # for i in range(int((graph.rank - 1)/self.divider)):  # przejście po wszystkich węzłach
                    ant._select_next()
                # ant.total_cost += graph.matrix[ant.tabu[-1]][ant.tabu[0]]  # doliczenie przejścia z ostatniego węzła do początkowego - cykl hamiltona - czy to nam potrzebne? - chyba nie
                if ant.total_cost < best_cost:
                    best_cost = ant.total_cost
                    best_solution = [] + ant.tabu
                # update pheromone
                ant._update_pheromone_delta()
            # print('best solution in gen #{}, cost: {}, path: {}'.format(gen, best_cost, best_solution))
            self._update_pheromone(graph, ants)
            # print('generation #{}, best cost: {}, path: {}'.format(gen, best_cost, best_solution))
        # if self.divider > 1:
        #     for i in range(self.divider):
        #         best_solution.extend(best_solution)
        return best_solution, best_cost


class _Ant(object):
    def __init__(self, aco: ACO, graph: GraphAS):
        self.colony = aco
        self.graph = graph
        self.total_cost = 0.0
        self.tabu = []  # lista tabu
        self.pheromone_delta = []  # lokalny przyrost feromonu
        self.allowed = [i for i in range(graph.rank)]  # dozwolone węzły do wyboru jako następny
        self.eta = [[0 if i == j else 1 / graph.matrix[i][j] for j in range(graph.rank)] for i in
                    range(graph.rank)]  # informacja heurystyczna
        start = random.randint(0, graph.rank - 1)  # rozpoczęcie z losowego węzła
        # start = 0  # rozpoczęcie z pierwszego - zawsze zagra oryginalną melodię
        self.tabu.append(start)
        self.current = start
        self.allowed.remove(start)

    def _select_next(self):
        denominator = 0
        for i in self.allowed:
            denominator += self.graph.pheromone[self.current][i] ** self.colony.alpha * self.eta[self.current][
                                                                                            i] ** self.colony.beta
        # noinspection PyUnusedLocal
        probabilities = [0 for i in range(self.graph.rank)]  # prawdopodobieństwa przemieszczenia się do węzła w kolejnym kroku
        for i in range(self.graph.rank):
            try:
                self.allowed.index(i)  # sprawdzenie czy lista dozwolonych węzłów zawiera i-ty
                probabilities[i] = self.graph.pheromone[self.current][i] ** self.colony.alpha * \
                    self.eta[self.current][i] ** self.colony.beta / denominator
            except ValueError:
                pass  # nie rób nic
        # wybierz następny węzeł przez ruletkę prawdopodobieństwa
        # selected = probabilities.index(max(probabilities))  # albo wybór po prostu największego prawdopodobieństwa
        selected = 0
        rand = random.random()
        for i, probability in enumerate(probabilities):
            rand -= probability
            if rand <= 0:
                selected = i
                break
        self.allowed.remove(selected)
        self.tabu.append(selected)
        self.total_cost += self.graph.matrix[self.current][selected]
        self.current = selected

    def _update_pheromone_delta(self):
        self.pheromone_delta = [[0 for j in range(self.graph.rank)] for i in range(self.graph.rank)]
        for _ in range(1, len(self.tabu)):
            i = self.tabu[_ - 1]
            j = self.tabu[_]
            self.pheromone_delta[i][j] = self.colony.Q / self.total_cost