"""Closed-route nearest-neighbour + 2-opt optimization for Kigali POIs."""
from __future__ import annotations
import json
import math
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
RNG_SEED = 2026
RANDOM_TRIALS = 1000


def haversine(a, b):
    r = 6371.0088
    la, lb = math.radians(a['lat']), math.radians(b['lat'])
    dlat, dlon = lb - la, math.radians(b['lon'] - a['lon'])
    h = math.sin(dlat / 2) ** 2 + math.cos(la) * math.cos(lb) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(min(1, math.sqrt(h)))


def matrix(points):
    return np.array([[haversine(a, b) for b in points] for a in points])


def distance(order, distances):
    return float(sum(distances[order[k], order[k + 1]] for k in range(len(order) - 1)))


def nearest_neighbor(distances):
    unvisited = set(range(1, len(distances)))
    order = [0]
    while unvisited:
        nxt = min(unvisited, key=lambda x: (distances[order[-1], x], x))
        order.append(nxt)
        unvisited.remove(nxt)
    return order + [0]


def two_opt(order, distances):
    route = order.copy()
    # The depot remains fixed at both endpoints. Reverse segments only for strict improvement.
    while True:
        best_gain, best_pair = 1e-10, None
        for i in range(1, len(route) - 2):
            for j in range(i + 1, len(route) - 1):
                before = distances[route[i-1], route[i]] + distances[route[j], route[j+1]]
                after = distances[route[i-1], route[j]] + distances[route[i], route[j+1]]
                gain = before - after
                if gain > best_gain:
                    best_gain, best_pair = gain, (i, j)
        if best_pair is None:
            return route
        i, j = best_pair
        route[i:j+1] = reversed(route[i:j+1])


def run():
    data = json.loads((ROOT / 'data/stops.json').read_text())
    points = [data['depot'], *data['stops']]
    dm = matrix(points)
    nearest = nearest_neighbor(dm)
    optimized = two_opt(nearest, dm)
    rng = np.random.default_rng(RNG_SEED)
    random_distances = []
    sample_order = None
    for trial in range(RANDOM_TRIALS):
        shuffled = rng.permutation(np.arange(1, len(points))).tolist()
        order = [0, *shuffled, 0]
        if trial == 0: sample_order = order
        random_distances.append(distance(order, dm))
    mean_random = float(np.mean(random_distances))
    optimum = distance(optimized, dm)
    result = {'source': data['source'], 'extractedAt': data['extractedAt'],
              'method': 'nearest neighbor followed by best-improvement 2-opt',
              'distanceMethod': 'Haversine great-circle distance, not road driving distance',
              'randomSeed': RNG_SEED, 'randomTrials': RANDOM_TRIALS,
              'depot': points[0], 'stops': points[1:],
              'nearestRoute': nearest, 'optimizedRoute': optimized, 'exampleRandomRoute': sample_order,
              'nearestKm': round(distance(nearest, dm), 3), 'optimizedKm': round(optimum, 3),
              'randomExampleKm': round(distance(sample_order, dm), 3),
              'randomMeanKm': round(mean_random, 3),
              'savingsPercent': round(100 * (mean_random - optimum) / mean_random, 1)}
    (ROOT / 'public').mkdir(exist_ok=True)
    (ROOT / 'public/route.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    plot(points, result)
    export_html(points, result)
    print(json.dumps({k: result[k] for k in ('optimizedKm', 'nearestKm', 'randomMeanKm', 'savingsPercent')}, indent=2))
    return result


def plot(points, result):
    fig, ax = plt.subplots(figsize=(10, 7), dpi=170)
    fig.patch.set_facecolor('#0d1020')
    ax.set_facecolor('#151b2b')
    route = result['optimizedRoute']
    x = [points[k]['lon'] for k in route]
    y = [points[k]['lat'] for k in route]
    ax.plot(x, y, color='#d5f49b', linewidth=2, zorder=2)
    ax.scatter(x[1:-1], y[1:-1], s=35, c='#d5f49b', zorder=3)
    ax.scatter(x[0], y[0], s=160, c='#ffffff', marker='s', zorder=4)
    for visit, k in enumerate(route[1:-1], 1):
        ax.annotate(str(visit), (points[k]['lon'], points[k]['lat']), xytext=(4, 4),
                    textcoords='offset points', color='#ffffff', fontsize=8)
    ax.set_title('Kigali | 20 stops, one optimized loop', color='white', fontsize=17, loc='left', pad=16)
    ax.set_xlabel('Longitude (° E)', color='#acb6c4')
    ax.set_ylabel('Latitude (° N)', color='#acb6c4')
    ax.tick_params(colors='#aeb8c7')
    for spine in ax.spines.values(): spine.set_color('#354154')
    ax.grid(alpha=.14, color='white')
    ax.text(.01, -.14, f"{result['optimizedKm']:.2f} km great-circle loop  |  {result['savingsPercent']:.1f}% shorter than random mean",
            transform=ax.transAxes, color='#d5f49b', fontsize=11)
    ax.text(.01, -.20, 'Points of interest: © OpenStreetMap contributors (ODbL). Straight lines are not road routes.',
            transform=ax.transAxes, color='#aeb8c7', fontsize=9)
    fig.subplots_adjust(bottom=.23)
    (ROOT / 'output').mkdir(exist_ok=True)
    fig.savefig(ROOT / 'output/kigali-route.png', facecolor=fig.get_facecolor(), bbox_inches='tight')
    plt.close(fig)


def export_html(points, result):
    payload = json.dumps({'points': points, 'route': result['optimizedRoute']}, ensure_ascii=False).replace('</', '<\\/')
    html = '''<!doctype html><html lang="en"><head><meta charset="UTF-8"><title>Kigali optimized route</title><meta name="viewport" content="width=device-width, initial-scale=1"><link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"><style>html,body,#map{height:100%;margin:0} .badge{position:absolute;top:20px;left:50px;z-index:999;background:#111928;color:#d5f49b;padding:13px 17px;border-radius:8px;font:700 14px sans-serif;box-shadow:0 5px 20px #0005}</style></head><body><div id="map"></div><div class="badge">Kigali · 20 stops · __DIST__ km straight-line loop</div><script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script><script>const data=__PAYLOAD__;const map=L.map('map').setView([-1.95,30.06],14);L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>'}).addTo(map);const pts=data.route.map(i=>[data.points[i].lat,data.points[i].lon]);L.polyline(pts,{color:'#5b8037',weight:5}).addTo(map);data.route.slice(0,-1).forEach((id,i)=>L.marker([data.points[id].lat,data.points[id].lon]).addTo(map).bindPopup((i===0?'Depot':'Stop '+i)+': '+data.points[id].name));map.fitBounds(pts,{padding:[30,30]});</script></body></html>'''
    html = html.replace('__PAYLOAD__', payload).replace('__DIST__', str(result['optimizedKm']))
    (ROOT / 'output/kigali-route.html').write_text(html)


if __name__ == '__main__':
    run()
