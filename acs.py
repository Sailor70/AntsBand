import numpy as np
import random


class GraphACS(object):
    def __init__(self, cost_matrix: list, N: int):
        """
        :param cost_matrix: cost matrix
        :param N: number of nodes
        :param pheromone: global pheromone
        """
        self.matrix = cost_matrix
        self.N = N
        cnn = self.nn_heuristic(cost_matrix, N)
        # self.initial_pheromone = [[1 / (N * cnn) for j in range(N)] for i in range(N)]
        self.initial_pheromone = [[self.put_pheromone(i, j) for j in range(N)] for i in range(N)]
        self.pheromone = self.initial_pheromone
        # heuristic value
        self.eta = [[0 if i == j else 1 / cost_matrix[i][j] for j in range(N)] for i in range(N)]

    def put_pheromone(self, i: int, j: int):  # zainicjowanie śladu feromonowego zgodnie z oryginalną melodią
        if j == i+1:
            return 10
        else:
            return 1 / (self.N * self.N)

    def nn_heuristic(self, cost_matrix: list, N: int):
        total_cost = 0
        unvisited = list(range(N))
        start = random.randint(0, N - 1)
        unvisited.remove(start)
        selected = start

        while unvisited:
            mincost = np.inf
            nearest = -1
            for i in unvisited:
                cost = cost_matrix[selected][i]
                if cost < mincost:
                    mincost = cost
                    nearest = i
            total_cost += mincost
            selected = nearest
            unvisited.remove(selected)
        total_cost += cost_matrix[selected][start]
        return total_cost


# Ant Colony System
class ACS(object):
    def __init__(self, n: int, m: int, alpha: float, beta: float, rho: float, phi: float, q_zero: float):
        """
        :param n: number of generations
        :param m: number of ants
        :param alpha: history coefficient
        :param beta: heuristic coefficient
        :param rho: decay coefficient
        :param phi: evaporation factor
        :param q_zero: greediness factor
        """
        self.n = n
        self.m = m
        self.alpha = alpha
        self.beta = beta
        self.rho = rho
        self.phi = phi
        self.q_zero = q_zero

    def solve(self, graph: GraphACS):
        best_cost = float('inf')
        best_solution = []
        for gen in range(self.n):
            print('Generation ', gen)
            ants = [Ant(self, graph) for i in range(self.m)]
            for ant in ants:
                ant.generate_tour()
                if ant.total_cost < best_cost:
                    best_cost = ant.total_cost
                    print('Best cost update: ', best_cost)
                    best_solution = [] + ant.tour
            self.update_pheromone(graph, ants, best_solution, best_cost)
        return best_solution, best_cost

    # Global update
    def update_pheromone(self, graph: GraphACS, ants: list, best: list, lbest):
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


class Ant(object):
    def __init__(self, aco: ACS, graph: GraphACS):
        self.aco = aco
        self.graph = graph
        self.total_cost = 0.0
        start = random.randint(0, graph.N - 1)
        self.current = start
        self.tour = [start]
        self.unvisited = [i for i in range(graph.N)]
        self.unvisited.remove(start)

    def generate_tour(self):
        for i in range(self.graph.N - 1):
            self.select_next_node()
            self.update_pheromone_local()
        self.update_last()

    def update_last(self):
        last = self.tour[0]
        self.tour.append(last)
        self.total_cost += self.graph.matrix[self.current][last]
        self.current = last
        self.update_pheromone_local()

    def update_pheromone_local(self):
        i = self.tour[-1]
        j = self.tour[-2]
        self.graph.pheromone[i][j] = (1 - self.aco.phi) * self.graph.pheromone[i][j] + self.aco.phi * \
                                     self.graph.initial_pheromone[i][j]

    def select_next_node(self):
        selected = self._select_node()
        self.unvisited.remove(selected)
        self.tour.append(selected)
        self.total_cost += self.graph.matrix[self.current][selected]
        self.current = selected

    def _select_node(self):
        selected = -1
        q = random.random()
        if (q < self.aco.q_zero):
            maxim = 0
            i = self.current
            for g in self.unvisited:
                rule = (self.graph.pheromone[i][g] ** self.aco.alpha) * (self.graph.eta[i][g] ** self.aco.beta)
                if rule > maxim:
                    maxim = rule
                    selected = g
        else:
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