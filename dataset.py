import json
import random
import math

random.seed(42)

# Lima districts with approximate center coordinates
districts = [
    {"id": "MIRAFLORES", "name": "Miraflores", "lat": -12.1219, "lng": -77.0282},
    {"id": "SAN_ISIDRO", "name": "San Isidro", "lat": -12.0979, "lng": -77.0358},
    {"id": "SURCO", "name": "Santiago de Surco", "lat": -12.1417, "lng": -76.9901},
    {"id": "LA_MOLINA", "name": "La Molina", "lat": -12.0796, "lng": -76.9406},
    {"id": "SAN_BORJA", "name": "San Borja", "lat": -12.1066, "lng": -77.0008},
    {"id": "LINCE", "name": "Lince", "lat": -12.0826, "lng": -77.0354},
    {"id": "JESUS_MARIA", "name": "Jesús María", "lat": -12.0749, "lng": -77.0469},
    {"id": "SAN_MIGUEL", "name": "San Miguel", "lat": -12.0773, "lng": -77.0851},
    {"id": "PUEBLO_LIBRE", "name": "Pueblo Libre", "lat": -12.0747, "lng": -77.0626},
    {"id": "MAGDALENA", "name": "Magdalena del Mar", "lat": -12.0905, "lng": -77.0698},
    {"id": "BARRANCO", "name": "Barranco", "lat": -12.1436, "lng": -77.0222},
    {"id": "CHORRILLOS", "name": "Chorrillos", "lat": -12.1681, "lng": -77.0200},
    {"id": "ATE", "name": "Ate", "lat": -12.0264, "lng": -76.9165},
    {"id": "SURQUILLO", "name": "Surquillo", "lat": -12.1115, "lng": -77.0178},
    {"id": "LIMA_CENTRO", "name": "Lima Centro (Cercado)", "lat": -12.0453, "lng": -77.0311},
    {"id": "SAN_MARTIN", "name": "San Martín de Porres", "lat": -12.0065, "lng": -77.0762},
    {"id": "CALLAO", "name": "Callao", "lat": -12.0565, "lng": -77.1186},
    {"id": "LA_VICTORIA", "name": "La Victoria", "lat": -12.0675, "lng": -77.0197},
    {"id": "RIMAC", "name": "Rímac", "lat": -12.0286, "lng": -77.0318},
    {"id": "SAN_JUAN_MIRAFLORES", "name": "San Juan de Miraflores", "lat": -12.1578, "lng": -76.9715},
]

road_types = ["avenida_principal", "calle_secundaria", "jiron", "pasaje", "via_expresa"]
traffic_levels = ["bajo", "medio", "alto", "muy_alto"]

def haversine_dist(lat1, lng1, lat2, lng2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))

nodes = []
node_id = 1

# Generate ~80 intersections per district = 1600 nodes total
intersections_per_district = 80

for district in districts:
    base_lat = district["lat"]
    base_lng = district["lng"]
    spread_lat = 0.012
    spread_lng = 0.015
    
    for i in range(intersections_per_district):
        lat = base_lat + random.uniform(-spread_lat, spread_lat)
        lng = base_lng + random.uniform(-spread_lng, spread_lng)
        
        street_names = [
            f"Av. {random.choice(['Los Pinos','Las Flores','La Marina','Arequipa','Javier Prado','Benavides','Angamos','República','Universitaria','Colonial','Brasil','Tacna','Abancay','Grau','28 de Julio','Santa Cruz','Salaverry','Paseo de la República'])}",
            f"Jr. {random.choice(['Huancayo','Cusco','Ica','Piura','Trujillo','Chiclayo','Puno','Tacna','Moquegua','Cajamarca','Ayacucho','Huánuco','Loreto','Ucayali'])}",
            f"Calle {random.choice(['Los Olivos','Las Begonias','Las Orquídeas','Los Tulipanes','Los Geranios','Los Lirios','Los Jazmines','Las Rosas','Los Claveles','Los Girasoles'])}"
        ]
        
        node = {
            "id": f"N{node_id:04d}",
            "distrito": district["id"],
            "nombre_distrito": district["name"],
            "latitud": round(lat, 6),
            "longitud": round(lng, 6),
            "calle_principal": random.choice(street_names),
            "tipo_via": random.choice(road_types),
            "nivel_trafico": random.choice(traffic_levels),
            "semaforo": random.choice([True, False]),
            "velocidad_promedio_kmh": random.randint(10, 60),
            "capacidad_vehiculos": random.randint(100, 800),
        }
        nodes.append(node)
        node_id += 1

# Generate edges (connections between nodes)
edges = []
edge_id = 1

node_map = {n["id"]: n for n in nodes}
node_list = nodes[:]

# Connect nodes within the same district (nearby ones)
district_nodes = {}
for n in nodes:
    d = n["distrito"]
    if d not in district_nodes:
        district_nodes[d] = []
    district_nodes[d].append(n)

# Intra-district connections
for d, dnodes in district_nodes.items():
    # Sort by lat then connect sequentially + some random cross connections
    sorted_nodes = sorted(dnodes, key=lambda x: (x["latitud"], x["longitud"]))
    for i in range(len(sorted_nodes) - 1):
        src = sorted_nodes[i]
        dst = sorted_nodes[i+1]
        dist_m = haversine_dist(src["latitud"], src["longitud"], dst["latitud"], dst["longitud"])
        speed = (src["velocidad_promedio_kmh"] + dst["velocidad_promedio_kmh"]) / 2
        travel_time = (dist_m / 1000) / speed * 60  # minutes
        
        traffic_mult = {"bajo": 1.0, "medio": 1.3, "alto": 1.8, "muy_alto": 2.5}
        avg_traffic = random.choice(list(traffic_mult.values()))
        
        edges.append({
            "id": f"E{edge_id:05d}",
            "origen": src["id"],
            "destino": dst["id"],
            "distancia_metros": round(dist_m, 1),
            "tiempo_viaje_min": round(travel_time * avg_traffic, 2),
            "tipo_via": random.choice(road_types),
            "direccion": random.choice(["bidireccional", "unidireccional"]),
            "congestion": random.choice(traffic_levels),
            "num_carriles": random.randint(1, 4),
        })
        edge_id += 1
    
    # Add some random intra-district connections
    for _ in range(20):
        src = random.choice(dnodes)
        dst = random.choice(dnodes)
        if src["id"] != dst["id"]:
            dist_m = haversine_dist(src["latitud"], src["longitud"], dst["latitud"], dst["longitud"])
            speed = (src["velocidad_promedio_kmh"] + dst["velocidad_promedio_kmh"]) / 2
            travel_time = max(0.1, (dist_m / 1000) / speed * 60)
            edges.append({
                "id": f"E{edge_id:05d}",
                "origen": src["id"],
                "destino": dst["id"],
                "distancia_metros": round(dist_m, 1),
                "tiempo_viaje_min": round(travel_time * random.uniform(1.0, 2.5), 2),
                "tipo_via": random.choice(road_types),
                "direccion": random.choice(["bidireccional", "unidireccional"]),
                "congestion": random.choice(traffic_levels),
                "num_carriles": random.randint(1, 4),
            })
            edge_id += 1

# Inter-district connections (major avenues connecting districts)
major_avenues = [
    ("MIRAFLORES", "SURQUILLO"), ("SURQUILLO", "SAN_BORJA"), ("SAN_BORJA", "SURCO"),
    ("MIRAFLORES", "BARRANCO"), ("BARRANCO", "CHORRILLOS"), ("SAN_ISIDRO", "MIRAFLORES"),
    ("SAN_ISIDRO", "LINCE"), ("LINCE", "JESUS_MARIA"), ("JESUS_MARIA", "PUEBLO_LIBRE"),
    ("PUEBLO_LIBRE", "SAN_MIGUEL"), ("SAN_MIGUEL", "CALLAO"), ("LIMA_CENTRO", "LA_VICTORIA"),
    ("LIMA_CENTRO", "RIMAC"), ("LIMA_CENTRO", "SAN_MARTIN"), ("ATE", "SAN_BORJA"),
    ("ATE", "LA_MOLINA"), ("SURCO", "LA_MOLINA"), ("SAN_JUAN_MIRAFLORES", "CHORRILLOS"),
    ("SAN_JUAN_MIRAFLORES", "SURCO"), ("MAGDALENA", "SAN_MIGUEL"), ("MAGDALENA", "MIRAFLORES"),
]

for d1, d2 in major_avenues:
    nodes_d1 = district_nodes.get(d1, [])
    nodes_d2 = district_nodes.get(d2, [])
    if nodes_d1 and nodes_d2:
        for _ in range(5):
            src = random.choice(nodes_d1)
            dst = random.choice(nodes_d2)
            dist_m = haversine_dist(src["latitud"], src["longitud"], dst["latitud"], dst["longitud"])
            speed = (src["velocidad_promedio_kmh"] + dst["velocidad_promedio_kmh"]) / 2
            travel_time = max(0.5, (dist_m / 1000) / speed * 60)
            edges.append({
                "id": f"E{edge_id:05d}",
                "origen": src["id"],
                "destino": dst["id"],
                "distancia_metros": round(dist_m, 1),
                "tiempo_viaje_min": round(travel_time * random.uniform(1.2, 2.8), 2),
                "tipo_via": "avenida_principal",
                "direccion": "bidireccional",
                "congestion": random.choice(["medio", "alto", "muy_alto"]),
                "num_carriles": random.randint(2, 6),
            })
            edge_id += 1

dataset = {
    "metadata": {
        "titulo": "Red Vial Urbana de Lima Metropolitana",
        "descripcion": "Dataset de intersecciones viales y conexiones para análisis de control de tráfico inteligente",
        "ciudad": "Lima, Perú",
        "fuente": "Datos sintéticos basados en la estructura real de Lima Metropolitana",
        "año": 2026,
        "total_nodos": len(nodes),
        "total_aristas": len(edges),
        "total_distritos": len(districts),
        "distritos_incluidos": [d["name"] for d in districts],
        "campos_nodo": ["id", "distrito", "nombre_distrito", "latitud", "longitud", "calle_principal", "tipo_via", "nivel_trafico", "semaforo", "velocidad_promedio_kmh", "capacidad_vehiculos"],
        "campos_arista": ["id", "origen", "destino", "distancia_metros", "tiempo_viaje_min", "tipo_via", "direccion", "congestion", "num_carriles"]
    },
    "nodos": nodes,
    "aristas": edges
}

def save_dataset(output_file="lima_traffic_dataset.json"):
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

def main():
    save_dataset()
    print(f"Nodos: {len(nodes)}")
    print(f"Aristas: {len(edges)}")
    print("Dataset generado exitosamente")

if __name__ == "__main__":
    main()
