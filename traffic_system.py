import json
from collections import defaultdict
import graphviz as gv


def load_dataset(path="lima_traffic_dataset.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def construir_lista_adyacencia(data):
    lista = defaultdict(list)
    for edge in data["aristas"]:
        origen = edge["origen"]
        destino = edge["destino"]
        lista[origen].append(destino)
        if edge["direccion"] == "bidireccional":
            lista[destino].append(origen)

    # Asegura que todos los nodos aparezcan aunque no tengan salida
    for node in data["nodos"]:
        lista[node["id"]] = lista[node["id"]]

    # Quita duplicados y ordena para salida estable
    salida = {}
    for vertice, adyacentes in lista.items():
        salida[vertice] = sorted(set(adyacentes))
    return salida


def dibujarGrafo(listaAdyacencia):
    grafo = gv.Graph()
    grafo.attr(rankdir="LR")
    listaAsignados = set()

    for vertice in listaAdyacencia:
        grafo.node(vertice)

    for vertice in listaAdyacencia:
        for adyacente in listaAdyacencia[vertice]:
            if (vertice, adyacente) not in listaAsignados:
                grafo.edge(vertice, adyacente)
                listaAsignados.add((adyacente, vertice))
    return grafo


def main():
    data = load_dataset()
    listaAdyacencia = construir_lista_adyacencia(data)

    print("listaAdyacencia = {")
    for vertice in sorted(listaAdyacencia.keys()):
        print(f'    "{vertice}": {listaAdyacencia[vertice]},')
    print("}")

    grafo = dibujarGrafo(listaAdyacencia)
    grafo.save("traffic_graph.gv")
    grafo.render("traffic_graph", format="png", cleanup=False)
    print("Grafo generado: traffic_graph.gv y traffic_graph.png")


if __name__ == "__main__":
    main()
