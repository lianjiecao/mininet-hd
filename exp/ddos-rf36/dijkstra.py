from collections import defaultdict


class DGraph:
  def __init__(self):
    self.nodes = set()
    self.edges = defaultdict(list)
    self.distances = {}

  def addVert(self, value):
    self.nodes.add(value)

  def addEdge(self, from_node, to_node, distance):
    self.edges[from_node].append(to_node)
    self.edges[to_node].append(from_node)
    self.distances[tuple(sorted([from_node, to_node]))] = distance


def dijsktraCompute(DGraph, initial):
  visited = {initial: 0}
  path = {}

  nodes = set(DGraph.nodes)

  while nodes: 
    min_node = None
    for node in nodes:
      if node in visited:
        if min_node is None:
          min_node = node
        elif visited[node] < visited[min_node]:
          min_node = node

    if min_node is None:
      break

    nodes.remove(min_node)
    current_weight = visited[min_node]

    for edge in DGraph.edges[min_node]:
      weight = current_weight + DGraph.distances[tuple(sorted([min_node, edge]))]
      if edge not in visited or weight < visited[edge]:
        visited[edge] = weight
        path[edge] = min_node

  return visited, path

if __name__ == '__main__':

  g = DGraph()
  for i in range(12):
    g.addVert(i)
  g.addEdge(5,4,1)
  g.addEdge(4,7,1)
  g.addEdge(4,10,1)
  g.addEdge(7,10,1)
  g.addEdge(10,6,1)
  g.addEdge(10,9,1)
  g.addEdge(6,3,1)
  g.addEdge(6,11,1)
  g.addEdge(9,1,1)
  g.addEdge(9,8,1)
  g.addEdge(9,11,1)
  g.addEdge(11,2,1)

  [v, p] = dijsktra(g, 5)
  print 'visited:', v
  print 'path:   ', p
