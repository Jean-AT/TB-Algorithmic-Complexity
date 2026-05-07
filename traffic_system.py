import json
import heapq
from collections import defaultdict


def load_dataset(path="lima_traffic_dataset.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_graph(data, weight_key="tiempo_viaje_min"):
    graph = defaultdict(list)
    for edge in data["aristas"]:
        src = edge["origen"]
        dst = edge["destino"]
        weight = edge[weight_key]
        graph[src].append((dst, weight))
        if edge["direccion"] == "bidireccional":
            graph[dst].append((src, weight))
    return graph


def dijkstra(graph, start, end):
    pq = [(0.0, start, [start])]
    best = {start: 0.0}

    while pq:
        cost, node, path = heapq.heappop(pq)
        if node == end:
            return cost, path
        if cost > best.get(node, float("inf")):
            continue
        for nxt, w in graph[node]:
            new_cost = cost + w
            if new_cost < best.get(nxt, float("inf")):
                best[nxt] = new_cost
                heapq.heappush(pq, (new_cost, nxt, path + [nxt]))
    return None, []


def main():
    data = load_dataset()
    graph = build_graph(data, weight_key="tiempo_viaje_min")

    start = data["nodos"][6]["id"]
    end = data["nodos"][-50]["id"]
    cost, route = dijkstra(graph, start, end)

    if route:
        print("Ruta óptima encontrada")
        print(f"Origen: {start}")
        print(f"Destino: {end}")
        print(f"Tiempo estimado: {cost:.2f} min")
        print("Ruta:", " -> ".join(route))
    else:
        print("No se encontró ruta entre los nodos seleccionados")


if __name__ == "__main__":
    main()
