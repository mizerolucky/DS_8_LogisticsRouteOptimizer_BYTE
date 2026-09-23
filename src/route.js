export function distance(a, b) {
  const rad = Math.PI / 180, R = 6371.0088;
  const la = a.lat * rad, lb = b.lat * rad, dlat = lb - la, dlon = (b.lon - a.lon) * rad;
  const h = Math.sin(dlat / 2) ** 2 + Math.cos(la) * Math.cos(lb) * Math.sin(dlon / 2) ** 2;
  return 2 * R * Math.asin(Math.min(1, Math.sqrt(h)));
}
export function routeDistance(route, byId) {
  return route.slice(1).reduce((sum, id, i) => sum + distance(byId[route[i]], byId[id]), 0);
}
export function nearestNeighbor(ids, byId) {
  const unvisited = new Set(ids), route = [0];
  while (unvisited.size) {
    let best = [...unvisited].sort((a, b) => distance(byId[route.at(-1)], byId[a]) - distance(byId[route.at(-1)], byId[b]) || a - b)[0];
    route.push(best); unvisited.delete(best);
  }
  return [...route, 0];
}
export function twoOpt(route, byId) {
  route = [...route];
  while (true) {
    let bestGain = 1e-10, pair = null;
    for (let i = 1; i < route.length - 2; i++) for (let j = i + 1; j < route.length - 1; j++) {
      const a = byId[route[i - 1]], b = byId[route[i]], c = byId[route[j]], d = byId[route[j + 1]];
      const gain = distance(a, b) + distance(c, d) - distance(a, c) - distance(b, d);
      if (gain > bestGain) {bestGain = gain; pair = [i, j]}
    }
    if (!pair) return route;
    const [i, j] = pair; route.splice(i, j - i + 1, ...route.slice(i, j + 1).reverse());
  }
}
export function randomBenchmark(ids, byId, trials = 250) {
  // Seeded, deterministic Fisher-Yates; each comparison includes the same selected stops.
  let state = 2026, total = 0;
  for (let t = 0; t < trials; t++) {
    const shuffle = [...ids];
    for (let k = shuffle.length - 1; k > 0; k--) {
      state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
      const j = state % (k + 1); [shuffle[k], shuffle[j]] = [shuffle[j], shuffle[k]];
    }
    total += routeDistance([0, ...shuffle, 0], byId);
  }
  return total / trials;
}
