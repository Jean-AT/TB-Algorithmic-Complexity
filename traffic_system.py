import json
import heapq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
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

def get_node_info(data):
    return {
        n["id"]: {
            "calle": n["calle_principal"],
            "lat": n["latitud"],
            "lng": n["longitud"],
            "distrito": n["nombre_distrito"],
            "distrito_id": n["distrito"],
        }
        for n in data["nodos"]
    }


def get_route_edges(data, route_nodes):
    route_set = set(zip(route_nodes, route_nodes[1:]))
    edges = []
    for edge in data["aristas"]:
        pair = (edge["origen"], edge["destino"])
        pair_rev = (edge["destino"], edge["origen"])
        if pair in route_set or (edge["direccion"] == "bidireccional" and pair_rev in route_set):
            edges.append(edge)
    return edges

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

def build_zone_graph(data, node_info, weight_key="tiempo_viaje_min"):
    """
    Construye un grafo reducido donde cada nodo representa
    una ZONA (distrito). El peso entre zonas es el promedio
    del tiempo de viaje de las aristas inter-zona.
    """
    zone_edges = defaultdict(list) 
    zone_nodes = defaultdict(set)  

    for n in data["nodos"]:
        zone_nodes[n["distrito"]].add(n["id"])

    for edge in data["aristas"]:
        src_zone = node_info[edge["origen"]]["distrito_id"]
        dst_zone = node_info[edge["destino"]]["distrito_id"]
        w = edge[weight_key]
        if src_zone != dst_zone:
            zone_edges[src_zone].append((dst_zone, w))
            if edge["direccion"] == "bidireccional":
                zone_edges[dst_zone].append((src_zone, w))

    averaged = defaultdict(list)
    for src_zone, neighbors in zone_edges.items():
        bucket = defaultdict(list)
        for dst_zone, w in neighbors:
            bucket[dst_zone].append(w)
        for dst_zone, weights in bucket.items():
            averaged[src_zone].append((dst_zone, sum(weights) / len(weights)))
    return averaged, zone_nodes

def dijkstra_zones(zone_graph, start_zone, end_zone):
    """Dijkstra ligero solo sobre el grafo de zonas (20 nodos max)."""
    pq = [(0.0, start_zone, [start_zone])]
    best = {start_zone: 0.0}
    while pq:
        cost, zone, path = heapq.heappop(pq)
        if zone == end_zone:
            return cost, path
        if cost > best.get(zone, float("inf")):
            continue
        for nxt, w in zone_graph[zone]:
            new_cost = cost + w
            if new_cost < best.get(nxt, float("inf")):
                best[nxt] = new_cost
                heapq.heappush(pq, (new_cost, nxt, path + [nxt]))
    return None, []

def local_dijkstra(graph, start, end, allowed_nodes):
    """
    Dijkstra restringido a un subconjunto de nodos (una zona o dos zonas).
    Permite salir del subconjunto SOLO hacia 'end' si no está en él.
    """
    pq = [(0.0, start, [start])]
    best = {start: 0.0}
    while pq:
        cost, node, path = heapq.heappop(pq)
        if node == end:
            return cost, path
        if cost > best.get(node, float("inf")):
            continue
        for nxt, w in graph[node]:
            if nxt not in allowed_nodes and nxt != end:
                continue
            new_cost = cost + w
            if new_cost < best.get(nxt, float("inf")):
                best[nxt] = new_cost
                heapq.heappush(pq, (new_cost, nxt, path + [nxt]))
    return None, []

def find_border_nodes(zone_nodes, graph, node_info, zone_a, zone_b):
    """
    Encuentra nodos frontera entre dos zonas adyacentes:
    nodos de zona_a que tienen al menos una arista hacia zona_b.
    """
    borders_a = set()
    borders_b = set()
    nodes_a = zone_nodes[zone_a]
    nodes_b = zone_nodes[zone_b]

    for n in nodes_a:
        for nxt, _ in graph[n]:
            if nxt in nodes_b:
                borders_a.add(n)
                borders_b.add(nxt)

    return borders_a, borders_b

def divide_and_conquer_route(graph, node_info, zone_graph, zone_nodes,
                              start, end):
    """
    Estrategia Divide y Vencerás:

    1. DIVIDIR   — Identifica la secuencia de zonas (distritos) que
                   conectan origen con destino usando el grafo de zonas.
    2. CONQUISTAR — Por cada par de zonas consecutivas, resuelve el
                    subproblema local: encontrar la mejor ruta dentro
                    de esa zona usando solo sus nodos.
    3. COMBINAR  — Encadena los segmentos locales en una ruta global
                   y recalcula el costo total real.
    """
    start_zone = node_info[start]["distrito_id"]
    end_zone   = node_info[end]["distrito_id"]
    if start_zone == end_zone:
        zone_path = [start_zone]
    else:
        _, zone_path = dijkstra_zones(zone_graph, start_zone, end_zone)
        if not zone_path:
            return None, []

    print(f"\n  [D&C] Zonas a recorrer ({len(zone_path)}): {' → '.join(zone_path)}")
    full_route  = [start]
    total_cost  = 0.0
    current_src = start

    for i in range(len(zone_path)):
        current_zone = zone_path[i]
        is_last_zone = (i == len(zone_path) - 1)

        if is_last_zone:
            allowed = zone_nodes[current_zone] | {end}
            cost_seg, seg = local_dijkstra(graph, current_src, end, allowed)
            if seg is None:
                remaining = set()
                for z in zone_path[i:]:
                    remaining |= zone_nodes[z]
                remaining.add(end)
                cost_seg, seg = local_dijkstra(graph, current_src, end, remaining)
            if not seg:
                return None, []
            total_cost += cost_seg
            full_route += seg[1:]
            break
        else:
            next_zone = zone_path[i + 1]
            borders_curr, borders_next = find_border_nodes(
                zone_nodes, graph, node_info, current_zone, next_zone
            )
            if not borders_curr:
                allowed = zone_nodes[current_zone] | zone_nodes[next_zone]
                best_cost = float("inf")
                best_seg  = []
                for entry in zone_nodes[next_zone]:
                    c, s = local_dijkstra(graph, current_src, entry, allowed)
                    if s and c < best_cost:
                        best_cost = c
                        best_seg  = s
                if not best_seg:
                    return None, []
                total_cost += best_cost
                full_route += best_seg[1:]
                current_src = full_route[-1]
            else:
                allowed = zone_nodes[current_zone] | borders_next
                best_cost  = float("inf")
                best_seg   = []
                best_entry = None
                for border in borders_curr:
                    c, s = local_dijkstra(graph, current_src, border, allowed)
                    if s and c < best_cost:
                        best_cost  = c
                        best_seg   = s
                        best_entry = border
                if not best_seg:
                    return None, []
                total_cost += best_cost
                full_route += best_seg[1:]
                current_src = full_route[-1]
    return total_cost, full_route

def plot_route(route, node_info, route_edges, start, end, cost,
               algo_name="Dijkstra", filename="ruta_optima.png",
               zone_path=None):

    G = nx.DiGraph()
    for nid in route:
        G.add_node(nid)
    for edge in route_edges:
        G.add_edge(edge["origen"], edge["destino"],
                   weight=round(edge["tiempo_viaje_min"], 2))

    pos = {nid: (node_info[nid]["lng"], node_info[nid]["lat"]) for nid in route}

    color_map = []
    for nid in G.nodes():
        if nid == start:
            color_map.append("#2ecc71")
        elif nid == end:
            color_map.append("#e74c3c")
        else:
            color_map.append("#3498db")

    fig, ax = plt.subplots(figsize=(15, 11))
    fig.patch.set_facecolor("#0f0f1a")
    ax.set_facecolor("#0f0f1a")

    nx.draw_networkx_edges(G, pos, ax=ax,
                           edge_color="#f39c12", width=2.5,
                           arrows=True, arrowsize=15,
                           connectionstyle="arc3,rad=0.1")
    nx.draw_networkx_nodes(G, pos, ax=ax,
                           node_color=color_map, node_size=120)
    nx.draw_networkx_labels(G, pos, {nid: nid for nid in G.nodes()},
                            ax=ax, font_size=6,
                            font_color="white", font_weight="bold")

    edge_labels = {(e["origen"], e["destino"]): f"{e['tiempo_viaje_min']:.1f}m"
                   for e in route_edges}
    nx.draw_networkx_edge_labels(G, pos, edge_labels, ax=ax,
                                 font_size=6, font_color="#f39c12",
                                 bbox=dict(boxstyle="round,pad=0.2",
                                           fc="#0f0f1a", alpha=0.7))

    legend_elements = [
        mpatches.Patch(color="#2ecc71", label=f"Origen : {start}"),
        mpatches.Patch(color="#e74c3c", label=f"Destino: {end}"),
        mpatches.Patch(color="#3498db", label="Nodos intermedios"),
    ]
    ax.legend(handles=legend_elements, loc="upper left",
              facecolor="#0f0f1a", labelcolor="white", fontsize=9)

    subtitle = ""
    if zone_path:
        subtitle = f"\nZonas: {' → '.join(zone_path)}"

    ax.set_title(
        f"[{algo_name}]  Ruta óptima Lima — {len(route)} nodos | "
        f"Tiempo: {cost:.2f} min{subtitle}",
        color="white", fontsize=11, fontweight="bold", pad=12)

    for spine in ax.spines.values():
        spine.set_edgecolor("#333")
    ax.tick_params(colors="gray")

    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()
    print(f"  Gráfico guardado: {filename}")

def print_route_table(route, node_info, start, end, cost, algo_name):
    print(f"\n{'='*60}")
    print(f"  {algo_name}")
    print(f"{'='*60}")
    print(f"  Origen : {start}  ({node_info[start]['distrito']})")
    print(f"  Destino: {end}  ({node_info[end]['distrito']})")
    print(f"  Tiempo : {cost:.2f} min  |  Nodos: {len(route)}")
    print(f"{'-'*60}")
    for i, nid in enumerate(route):
        info = node_info[nid]
        tag = " ◀ ORIGEN" if nid == start else (" ◀ DESTINO" if nid == end else "")
        print(f"  [{i+1:>2}] {nid} | {info['calle']:<38} | {info['distrito']}{tag}")
    print(f"{'='*60}")

def main():
    data      = load_dataset()
    graph     = build_graph(data, weight_key="tiempo_viaje_min")
    node_info = get_node_info(data)

    start = data["nodos"][1]["id"]
    end   = data["nodos"][21]["id"]
    # ── Algoritmo 1: Dijkstra clásico ────────────────────────────────
    cost_d, route_d = dijkstra(graph, start, end)
    if route_d:
        print_route_table(route_d, node_info, start, end, cost_d,
                          "ALGORITMO 1 — DIJKSTRA CLÁSICO")
        edges_d = get_route_edges(data, route_d)
        plot_route(route_d, node_info, edges_d, start, end, cost_d,
                   algo_name="Dijkstra", filename="ruta_dijkstra.png")
    else:
        print("Dijkstra: no se encontró ruta.")
    # ── Algoritmo 2: Divide y Vencerás por zonas ─────────────────────
    zone_graph, zone_nodes = build_zone_graph(data, node_info)
    cost_dc, route_dc = divide_and_conquer_route(
        graph, node_info, zone_graph, zone_nodes, start, end
    )
    if route_dc:
        # Recalcular zona_path para el título del gráfico
        start_zone = node_info[start]["distrito_id"]
        end_zone   = node_info[end]["distrito_id"]
        _, zone_path = dijkstra_zones(zone_graph, start_zone, end_zone)

        print_route_table(route_dc, node_info, start, end, cost_dc,
                          "ALGORITMO 2 — DIVIDE Y VENCERÁS (ZONAS)")
        edges_dc = get_route_edges(data, route_dc)
        plot_route(route_dc, node_info, edges_dc, start, end, cost_dc,
                   algo_name="Divide y Vencerás",
                   filename="ruta_dyv.png",
                   zone_path=zone_path)
    else:
        print("D&C: no se encontró ruta.")
    # ── Comparación final ─────────────────────────────────────────────
    if route_d and route_dc:
        print(f"\n{'─'*60}")
        print(f"  COMPARACIÓN")
        print(f"{'─'*60}")
        print(f"  Dijkstra clásico  : {cost_d:.2f} min  ({len(route_d)} nodos)")
        print(f"  Divide y Vencerás : {cost_dc:.2f} min  ({len(route_dc)} nodos)")
        diff = abs(cost_d - cost_dc)
        mejor = "Dijkstra" if cost_d <= cost_dc else "D&C"
        print(f"  Diferencia        : {diff:.2f} min  →  Mejor: {mejor}")
        print(f"{'─'*60}\n")


if __name__ == "__main__":
    main()