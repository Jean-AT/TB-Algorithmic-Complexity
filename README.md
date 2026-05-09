# Intelligent Traffic Control System — Metropolitan Lima

Analysis and optimization of road routes in Lima using weighted graphs based on a synthetic dataset of 1,600 intersections and 20 districts.

## File

### `dataset.py`
Generates the `lima_traffic_dataset.json` file. Creates 1,600 nodes distributed across 20 districts with approximate real-world coordinates, traffic attributes (traffic lights, speed, congestion), and edges with distances calculated using the Haversine formula. Run this script first, before any other scripts.

### `traffic_system.py`
Main system. Loads the dataset, constructs the graph, and runs two algorithms to find the optimal path between two nodes. Prints the streets traversed (`main_street` for each node) to the console and generates PNG images with the geographic visualization.

## Algorithms

### 1. Dijkstra
Greedy algorithm with a priority queue (min-heap). It always expands the node with the lowest cumulative cost until it reaches the destination. It guarantees the global optimal solution.
- **Time:** `min_travel_time`
- **Complexity:** O((V + E) log V)
- **Output:** `dijkstra_path.png`

### 2. Divide and Conquer by Zones
A three-phase hierarchical approach:
- **Divide** — Find the sequence of districts (zones) that connects the origin to the destination using a compressed graph of ~20 nodes.
- **Conquer** — Solve the local subproblem in each zone, finding the best boundary node for crossing between districts.
- **Combine** — Chain the local segments into a global route and sum the actual cost.
- **Output:** `ruta_dyv.png`


## Install

```bash
pip install networkx matplotlib scipy
```

| Package      | Use                                         |
|--------------|---------------------------------------------|
| `networkx`   | Construction and visualization of the graph |
| `matplotlib` | Rendering PNG images                        |
| `scipy`      | Node positioning layout                     |


## Execution

```bash
# 1. Generate the dataset
python dataset.py

# 2. Run the routing system
python traffic_system.py
```
## IA use

- The team declarate use AI ('ChatGPT') in the file `dataset.py` for the structure for the dataset `districts, major_avenues` to get a real data of avenues and districts
- We use the AI in `traffic_system.py` in the function `plot_route` to use plot_routeplot_route `matplotlib`,`networkx` and to make a leyend for the colors nodes, lines and some about to make a good UX

**Output files:**
- `dijkstra_route.png` — route found by Dijkstra
- `dyv_route.png` — route found by Divide and Conquer