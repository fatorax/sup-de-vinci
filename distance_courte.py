import networkx as nx
import matplotlib.pyplot as plt


class Graph:
    def __init__(self, size):
        self.adj_matrix = [[0] * size for _ in range(size)]
        self.size = size
        self.vertex_data = [''] * size

    def add_edge(self, u, v, weight):
        if 0 <= u < self.size and 0 <= v < self.size:
            self.adj_matrix[u][v] = weight
            #self.adj_matrix[v][u] = weight  # For undirected graph

    def add_vertex_data(self, vertex, data):
        if 0 <= vertex < self.size:
            self.vertex_data[vertex] = data

    def bellman_ford(self, start_vertex_data):
        start_vertex = self.vertex_data.index(start_vertex_data)
        distances = [float('inf')] * self.size
        predecessors = [None] * self.size
        distances[start_vertex] = 0

        for i in range(self.size - 1):
            for u in range(self.size):
                for v in range(self.size):
                    if self.adj_matrix[u][v] != 0:
                        if distances[u] + self.adj_matrix[u][v] < distances[v]:
                            distances[v] = distances[u] + self.adj_matrix[u][v]
                            predecessors[v] = u
                            print(f"Relaxing edge {self.vertex_data[u]}-{self.vertex_data[v]}, Updated distance to {self.vertex_data[v]}: {distances[v]}")

        self.predecessors = predecessors
        return distances

    def draw(self, distances=None, predecessors=None):
        graph = nx.DiGraph()
        for i, label in enumerate(self.vertex_data):
            graph.add_node(label)
        for u in range(self.size):
            for v in range(self.size):
                if self.adj_matrix[u][v] != 0:
                    graph.add_edge(self.vertex_data[u], self.vertex_data[v], weight=self.adj_matrix[u][v])

        shortest_path_edges = set()
        if predecessors:
            for v, u in enumerate(predecessors):
                if u is not None:
                    shortest_path_edges.add((self.vertex_data[u], self.vertex_data[v]))

        pos = nx.circular_layout(graph)
        edge_colors = ['crimson' if e in shortest_path_edges else 'gray' for e in graph.edges()]
        edge_widths = [2.5 if e in shortest_path_edges else 1 for e in graph.edges()]

        plt.figure(figsize=(7, 6))
        nx.draw_networkx_nodes(graph, pos, node_color='lightblue', node_size=800)
        nx.draw_networkx_edges(graph, pos, edge_color=edge_colors, width=edge_widths,
                                connectionstyle='arc3,rad=0.1', arrowsize=20)
        nx.draw_networkx_edge_labels(graph, pos, edge_labels=nx.get_edge_attributes(graph, 'weight'))

        labels = {}
        for i, label in enumerate(self.vertex_data):
            labels[label] = f"{label}\n({distances[i]})" if distances else label
        nx.draw_networkx_labels(graph, pos, labels=labels, font_size=10, font_weight='bold')

        plt.title("Graphe et arbre des plus courts chemins (Bellman-Ford)")
        plt.axis('off')
        plt.tight_layout()
        plt.savefig('graph.png', dpi=150)
        plt.show()

g = Graph(5)

g.add_vertex_data(0, 'A')
g.add_vertex_data(1, 'B')
g.add_vertex_data(2, 'C')
g.add_vertex_data(3, 'D')
g.add_vertex_data(4, 'E')

g.add_edge(3, 0, 4)  # D -> A, weight 4
g.add_edge(3, 2, 7)  # D -> C, weight 7
g.add_edge(3, 4, 3)  # D -> E, weight 3
g.add_edge(0, 2, 4)  # A -> C, weight 4
g.add_edge(2, 0, -3) # C -> A, weight -3
g.add_edge(0, 4, 5)  # A -> E, weight 5
g.add_edge(4, 2, 3)  # E -> C, weight 3
g.add_edge(1, 2, -4) # B -> C, weight -4
g.add_edge(4, 1, 2)  # E -> B, weight 2

# Running the Bellman-Ford algorithm from D to all vertices
print("\nThe Bellman-Ford Algorithm starting from vertex D:")
distances = g.bellman_ford('D')
for i, d in enumerate(distances):
    print(f"Distance from D to {g.vertex_data[i]}: {d}")

g.draw(distances=distances, predecessors=g.predecessors)