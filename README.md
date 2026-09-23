# Wayline — Kigali Route Optimizer

An interactive **AVIP 2026 Data Science Task 8** project that visits 20 real Kigali locations and returns to a starting point. It uses nearest neighbor to build a tour and best-improvement 2-opt to shorten it. Visitors can change the stops and optimize a new route in the browser.

## Results

| Closed route visiting 20 destinations | Great-circle distance |
| --- | ---: |
| Nearest-neighbor starting route | 11.261 km |
| 2-opt improved route | **10.007 km** |
| Mean of 1,000 seeded random tours | 24.387 km |

The optimized route is **59.0% shorter** than the mean randomized tour under the same distance measure. This is a comparison to random order, not a claim of globally optimal routing or real-road driving savings.

## Data and measurement

[`data/stops.json`](data/stops.json) contains **20 named delivery drop-off coordinates and one depot** from [OpenStreetMap's map API](https://api.openstreetmap.org/api/0.6/map?bbox=30.05,-1.96,30.07,-1.94), extracted on September 23, 2026. It records each OpenStreetMap node ID, name, category, latitude, and longitude. Points were drawn deterministically from named amenities in the central Kigali bounding box, with farthest-first sampling to spread the stops. These are real map locations; the deliveries and the depot role are hypothetical. Data © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), available under the ODbL. Run `python scripts/extract_stops.py` to refresh the snapshot; future edits to OpenStreetMap may alter the selected points.

The distance matrix uses **Haversine great-circle kilometers**, so map lines connect coordinates directly. It does not calculate roads, traffic, travel time, or turn-by-turn routes. The heuristic might have a better route than the one it found. All comparisons include a return leg to the same depot and visit the same stops.

## Reproduce

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/optimize.py
```

This reads the committed location snapshot and regenerates [`public/route.json`](public/route.json), the plotted route PNG, and the standalone interactive HTML map. `scripts/optimize.py` uses seed 2026 and 1,000 randomized tours for the documented benchmark. The web app computes a new route with the same nearest-neighbor + 2-opt steps whenever you change its selected stops. For a changed subset, its on-page randomized comparison uses 250 seeded tours.

```bash
npm install
npm run dev
```

Deploy the repository as a **Vite** project on Vercel (`npm run build`, output `dist`). No backend, API key, or database is required. Map tiles are loaded from OpenStreetMap with visible attribution; the plotted route and markers remain driven by the committed coordinate data.

## Deliverables

- [`scripts/optimize.py`](scripts/optimize.py) — distance calculation, nearest neighbor, 2-opt, randomized baseline, and exports.
- [`scripts/extract_stops.py`](scripts/extract_stops.py) — reproducible OpenStreetMap point extraction.
- [`data/stops.json`](data/stops.json) — 20 real coordinates plus depot, names, node IDs, and source.
- [`output/kigali-route.html`](output/kigali-route.html) — standalone interactive Leaflet map.
- [`output/kigali-route.png`](output/kigali-route.png) — final plotted route preview.
- [`public/route.json`](public/route.json) and `src/` — benchmark snapshot and React route planner.
