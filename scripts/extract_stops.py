"""Snapshot named OpenStreetMap POIs inside a Kigali city-centre bounding box."""
import datetime
import json
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from math import cos, radians

ROOT = Path(__file__).resolve().parents[1]
BBOX = '30.05,-1.96,30.07,-1.94'  # west,south,east,north
SOURCE = 'https://api.openstreetmap.org/api/0.6/map?bbox=' + BBOX
AMENITIES = {'restaurant', 'cafe', 'school', 'hospital', 'pharmacy', 'bank', 'fuel', 'supermarket', 'fast_food'}


def extract(xml):
    eligible = []
    for node in ET.fromstring(xml).findall('node'):
        tags = {tag.attrib['k']: tag.attrib['v'] for tag in node.findall('tag')}
        if tags.get('name') and tags.get('amenity') in AMENITIES:
            eligible.append({'osmId': int(node.attrib['id']), 'name': tags['name'],
                             'category': tags['amenity'], 'lat': float(node.attrib['lat']),
                             'lon': float(node.attrib['lon'])})
    depot = next(p for p in eligible if p['name'] == 'SP City Centre')
    remaining = [p for p in eligible if p['osmId'] != depot['osmId']]
    # Deterministic farthest-first sampling gives 20 spatially spread, real POIs.
    selected = [depot]
    def squared(a, b):
        return (a['lat'] - b['lat']) ** 2 + (cos(radians(a['lat'])) * (a['lon'] - b['lon'])) ** 2
    for _ in range(20):
        point = max(remaining, key=lambda p: (min(squared(p, q) for q in selected), -p['osmId']))
        selected.append(point)
        remaining.remove(point)
    return {'source': SOURCE, 'extractedAt': datetime.datetime.now(datetime.timezone.utc).date().isoformat(),
            'note': 'Locations are real OSM points of interest; deliveries and depot are hypothetical.',
            'depot': {**selected[0], 'id': 0},
            'stops': [{**p, 'id': index} for index, p in enumerate(selected[1:], 1)]}


if __name__ == '__main__':
    request = urllib.request.Request(SOURCE, headers={'User-Agent': 'EchoLogisticsDemo/1.0 (educational data snapshot)'})
    with urllib.request.urlopen(request, timeout=60) as response:
        data = extract(response.read())
    path = ROOT / 'data/stops.json'
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
    print(f"Saved {len(data['stops'])} drop-off coordinates from {SOURCE}")
