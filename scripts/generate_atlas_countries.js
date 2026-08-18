const fs = require('fs');
const path = require('path');
const vm = require('vm');

const SRC_GEOJSON = path.join(__dirname, 'geodata', 'ne_10m_admin_0_countries.geojson');
const OLD_COUNTRIES_JS = path.join(__dirname, '..', 'web', 'static', 'js', 'atlas-countries.js');
const OUT_HI_JS = path.join(__dirname, '..', 'web', 'static', 'js', 'atlas-countries.js');
const OUT_LO_JS = path.join(__dirname, '..', 'web', 'static', 'js', 'atlas-countries-lo.js');

const SIMPLIFY_TOLERANCE_DEG = 0.006;
const SIMPLIFY_TOLERANCE_LO_DEG = 0.09;
const MIN_RING_AREA_LO_DEG2 = 0.05;
const MIN_RING_POINTS = 4;
const MIN_RING_AREA_DEG2 = 0.0004;

function toKey(name) {
    return name.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
}

function loadOldHeights() {
    try {
        const src = fs.readFileSync(OLD_COUNTRIES_JS, 'utf8');
        const sandbox = {};
        vm.createContext(sandbox);
        vm.runInContext(src, sandbox);
        const countries = vm.runInContext('countries', sandbox);
        const heights = {};
        for (const k in countries) heights[k] = countries[k].height;
        return heights;
    } catch (e) {
        return {};
    }
}

function ringArea(ring) {
    let area = 0;
    for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
        area += ring[j][0] * ring[i][1] - ring[i][0] * ring[j][1];
    }
    return Math.abs(area / 2);
}

function perpendicularDistance(pt, lineStart, lineEnd) {
    const [x, y] = pt;
    const [x1, y1] = lineStart;
    const [x2, y2] = lineEnd;
    const dx = x2 - x1, dy = y2 - y1;
    const len2 = dx * dx + dy * dy;
    if (len2 === 0) return Math.hypot(x - x1, y - y1);
    const t = ((x - x1) * dx + (y - y1) * dy) / len2;
    const projX = x1 + t * dx, projY = y1 + t * dy;
    return Math.hypot(x - projX, y - projY);
}

function douglasPeucker(points, epsilon) {
    if (points.length < 3) return points.slice();
    let maxDist = 0, maxIdx = 0;
    const first = points[0], last = points[points.length - 1];
    for (let i = 1; i < points.length - 1; i++) {
        const d = perpendicularDistance(points[i], first, last);
        if (d > maxDist) { maxDist = d; maxIdx = i; }
    }
    if (maxDist > epsilon) {
        const left = douglasPeucker(points.slice(0, maxIdx + 1), epsilon);
        const right = douglasPeucker(points.slice(maxIdx), epsilon);
        return left.slice(0, -1).concat(right);
    }
    return [first, last];
}

function simplifyRing(ring, epsilon) {
    const deduped = [ring[0]];
    for (let i = 1; i < ring.length; i++) {
        const prev = deduped[deduped.length - 1];
        if (Math.abs(ring[i][0] - prev[0]) > 1e-9 || Math.abs(ring[i][1] - prev[1]) > 1e-9) {
            deduped.push(ring[i]);
        }
    }
    if (deduped.length < 4) return deduped;
    const open = deduped.slice(0, -1);
    const simplified = douglasPeucker(open, epsilon);
    return simplified;
}

function encodeRing(pts) {
    const lat = new Array(pts.length);
    const lon = new Array(pts.length);
    let prevLat = 0, prevLon = 0;
    for (let i = 0; i < pts.length; i++) {
        const qLon = Math.round(pts[i][0] * 1000);
        const qLat = Math.round(pts[i][1] * 1000);
        lon[i] = qLon - prevLon;
        lat[i] = qLat - prevLat;
        prevLon = qLon;
        prevLat = qLat;
    }
    return { lat: lat, lon: lon };
}

function extractExteriorRings(geometry) {
    const rings = [];
    if (geometry.type === 'Polygon') {
        if (geometry.coordinates[0]) rings.push(geometry.coordinates[0]);
    } else if (geometry.type === 'MultiPolygon') {
        for (const poly of geometry.coordinates) {
            if (poly[0]) rings.push(poly[0]);
        }
    }
    return rings;
}

function main() {
    const geo = JSON.parse(fs.readFileSync(SRC_GEOJSON, 'utf8'));
    const oldHeights = loadOldHeights();

    const output = {};
    const outputLo = {};
    let totalPointsLo = 0;
    let totalPoints = 0;
    let totalRings = 0;
    let droppedRings = 0;

    for (const feature of geo.features) {
        const props = feature.properties;
        const name = props.ADMIN || props.NAME || props.SOVEREIGNT;
        if (!name) continue;
        const key = toKey(name);

        const rawRings = extractExteriorRings(feature.geometry);
        const polygons = [];

        const polygonsLo = [];

        for (const ring of rawRings) {
            const area = ringArea(ring);
            if (area < MIN_RING_AREA_DEG2 && ring.length < 20) { droppedRings++; continue; }

            const simplified = simplifyRing(ring, SIMPLIFY_TOLERANCE_DEG);
            if (simplified.length < MIN_RING_POINTS) { droppedRings++; continue; }

            polygons.push(encodeRing(simplified));
            totalPoints += simplified.length;
            totalRings++;

            if (area >= MIN_RING_AREA_LO_DEG2) {
                const lo = simplifyRing(ring, SIMPLIFY_TOLERANCE_LO_DEG);
                if (lo.length >= MIN_RING_POINTS) {
                    polygonsLo.push(encodeRing(lo));
                    totalPointsLo += lo.length;
                }
            }
        }

        if (!polygons.length) continue;

        polygons.sort((a, b) => b.lat.length - a.lat.length);
        polygonsLo.sort((a, b) => b.lat.length - a.lat.length);

        const height = oldHeights[key] !== undefined ? oldHeights[key] : Math.round((0.35 + (hashStr(key) % 55) / 100) * 100) / 100;

        if (output[key]) {
            output[key].polygons = output[key].polygons.concat(polygons);
        } else {
            output[key] = { polygons: polygons, height: height };
        }
        if (polygonsLo.length) {
            if (outputLo[key]) {
                outputLo[key].polygons = outputLo[key].polygons.concat(polygonsLo);
            } else {
                outputLo[key] = { polygons: polygonsLo, height: height };
            }
        }
    }

    function hashStr(s) {
        let h = 0;
        for (let i = 0; i < s.length; i++) h = (Math.imul(31, h) + s.charCodeAt(i)) | 0;
        return Math.abs(h);
    }

    fs.writeFileSync(OUT_HI_JS, 'var atlasCountriesHi=' + JSON.stringify(output) + ';\n', 'utf8');
    fs.writeFileSync(OUT_LO_JS, 'var atlasCountriesLo=' + JSON.stringify(outputLo) + ';\n', 'utf8');

    const hiStats = fs.statSync(OUT_HI_JS);
    const loStats = fs.statSync(OUT_LO_JS);
    console.log('countries hi:', Object.keys(output).length, '| lo:', Object.keys(outputLo).length);
    console.log('rings kept:', totalRings, '| dropped (tiny):', droppedRings);
    console.log('points  hi:', totalPoints, '| lo:', totalPointsLo);
    console.log('HI size:', (hiStats.size / 1024 / 1024).toFixed(2), 'MB');
    console.log('LO size:', (loStats.size / 1024).toFixed(0), 'KB');
}

main();
