import random


class GraphACS(object):
    def __init__(self, cost_matrix: list, N: int, sigma: float):
        """
        :param cost_matrix: macierz kosztów
        :param N: liczba węzłów
        :param pheromone: globalny feromon
        """
        self.cost_matrix = cost_matrix
        self.N = N
        self.sigma = sigma
        self.initial_pheromone = [[self.put_pheromone(i, j) for j in range(N)] for i in range(N)]
        self.pheromone = self.initial_pheromone
        self.eta = [[0 if i == j else 1 / cost_matrix[i][j] for j in range(N)] for i in range(N)]  # informacja heurystyczna

    def put_pheromone(self, i: int, j: int):  # zainicjowanie śladu feromonowego zgodnie z oryginalną melodią
        if j == i+1:
            return self.sigma
        else:
            return 1 / (self.N * self.N)


# Ant Colony System
class ACS(object):
    def __init__(self, generations: int, ant_count: int, alpha: float, beta: float, rho: float, phi: float, q_zero: float):
        """
        :param generations: liczba iteracji
        :param ant_count: liczba mrówek
        :param alpha: ważność feromonu
        :param beta: ważność informacji heurystycznej
        :param rho: współczynnik zaniku (globalne odparowanie)
        :param phi: współczynnik odparowania śladu feromonowego (lokalny)
        :param q_zero: czynnik chciwości
        """

        self.generations = generations
        self.ant_count = ant_count
        self.alpha = alpha  # alpha = 1 gdy chcemy oryginalną forme algorytmu
        self.beta = beta
        self.rho = rho
        self.phi = phi
        self.q_zero = q_zero

    def solve(self, graph: GraphACS):
        best_cost = float('inf')
        best_solution = []
        for gen in range(self.generations):
            ants = [AntACS(self, graph) for i in range(self.ant_count)]
            for ant in ants:
                ant.generate_path()
                if ant.total_cost < best_cost:
                    best_cost = ant.total_cost
                    best_solution = [] + ant.tabu
            self._update_global_pheromone(graph, best_solution, best_cost)
        return best_solution, best_cost

    def _update_global_pheromone(self, graph: GraphACS, best: list, lbest):
        for i, row in enumerate(graph.pheromone):
            for j, _ in enumerate(row):
                if self._edge_in_tour(i, j, best):
                    graph.pheromone[i][j] = (1 - self.rho) * graph.pheromone[i][j] + self.rho * (1 / lbest)

    def _edge_in_tour(self, i: int, j: int, tour: list):
        prev = -1
        for k in tour:
            if (prev == i and k == j) or (prev == j and k == i):
                return True
            prev = k
        return False


class AntACS(object):
    def __init__(self, aco: ACS, graph: GraphACS):
        self.aco = aco
        self.graph = graph
        self.total_cost = 0.0
        start = random.randint(0, graph.N - 1)
        self.current = start
        self.tabu = [start]
        self.unvisited = [i for i in range(graph.N)]
        self.unvisited.remove(start)

    def generate_path(self):
        for i in range(self.graph.N - 1):
            selected = self._select_next_node()
            self.unvisited.remove(selected)
            self.tabu.append(selected)
            self.total_cost += self.graph.cost_matrix[self.current][selected]
            self.current = selected
            self._update_pheromone_local()

    def _select_next_node(self):
        selected = 0
        q = random.random()
        if q <= self.aco.q_zero:  # eksploatacja
            max_val = 0
            i = self.current
            for g in self.unvisited:
                val = (self.graph.pheromone[i][g] ** self.aco.alpha) * (self.graph.eta[i][g] ** self.aco.beta)
                if val > max_val:
                    max_val = val
                    selected = g
        else:  # eksploracja
            probabilities = self._calculate_probabilities()
            for i, probability in enumerate(probabilities):
                q -= probability
                if q <= 0:
                    selected = i
                    break
        return selected

    def _calculate_probabilities(self):
        probabilities = [0 for i in range(self.graph.N)]
        denom = sum(self._prob_aux(l) for l in self.unvisited)
        for j in range(self.graph.N):
            if j in self.unvisited:
                probabilities[j] = self._prob_aux(j) / denom
        return probabilities

    def _prob_aux(self, i: int):
        return self.graph.pheromone[self.current][i] ** self.aco.alpha * self.graph.eta[self.current][
            i] ** self.aco.beta

    def _update_pheromone_local(self):
        i = self.tabu[-1]  # ostatni element
        j = self.tabu[-2]  # przedostatni element
        self.graph.pheromone[i][j] = (1 - self.aco.phi) * self.graph.pheromone[i][j] + self.aco.phi * \
                                     self.graph.initial_pheromone[i][j]