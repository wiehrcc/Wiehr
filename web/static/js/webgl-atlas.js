
(function() {
    'use strict';

    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) || window.innerWidth <= 768;

    const REGIONS = [
        { id: 'europe', name: 'Europe', latMin: 34, latMax: 72, lonMin: -12, lonMax: 42 },
        { id: 'asia', name: 'Asia', latMin: 5, latMax: 60, lonMin: 42, lonMax: 145 },
        { id: 'africa', name: 'Africa', latMin: -36, latMax: 38, lonMin: -20, lonMax: 55 },
        { id: 'north_america', name: 'N. America', latMin: 15, latMax: 72, lonMin: -170, lonMax: -50 },
        { id: 'south_america', name: 'S. America', latMin: -56, latMax: 15, lonMin: -85, lonMax: -30 },
        { id: 'oceania', name: 'Oceania', latMin: -50, latMax: 0, lonMin: 100, lonMax: 180 },
        { id: 'russia', name: 'Russia & CIS', latMin: 40, latMax: 78, lonMin: 19, lonMax: 180,
          countries: ['russia', 'belarus', 'kazakhstan', 'ukraine', 'moldova', 'armenia',
                      'azerbaijan', 'georgia', 'kyrgyzstan', 'tajikistan', 'turkmenistan',
                      'uzbekistan'] },
        { id: 'middle_east', name: 'Middle East', latMin: 12, latMax: 42, lonMin: 25, lonMax: 75,
          countries: ['turkey', 'cyprus', 'northern_cyprus', 'syria', 'lebanon', 'israel',
                      'palestine', 'jordan', 'iraq', 'iran', 'saudi_arabia', 'yemen', 'oman',
                      'united_arab_emirates', 'qatar', 'bahrain', 'kuwait'] },
    ];

    const LERP_SPEED = isMobile ? 0.16 : 0.14;
    const DRAG_SCALE = isMobile ? 0.9 : 0.7;
    const TOUCH_DRAG_SCALE = 0.9;


    const MARKER_SIZE = 9;

    const ZOOM_FACTOR_IN = 0.86;
    const ZOOM_FACTOR_OUT = 1.16;
    const MIN_LON_SPAN = 8;
    const MAX_LON_SPAN = 400;

    let canvas, ctx;
    let locationDots = [];
    let countryRegionMap = {};
    let polygonRegionMap = {};
    let locationCountryMap = {};

    function computeWorldView() {
        const asp = (canvas ? canvas.width / canvas.height : window.innerWidth / window.innerHeight) || 1.8;
        const zoomIn = window.innerWidth <= 640 ? 1.5 : 1;
        const lonSpan = 360 / zoomIn;
        const latSpan = (360 / asp) / zoomIn;
        return {
            lonMin: -lonSpan / 2,
            lonMax: lonSpan / 2,
            latMin: 15 - latSpan / 2,
            latMax: 15 + latSpan / 2
        };
    }
    let WORLD_VIEW = { lonMin: -180, lonMax: 180, latMin: -75, latMax: 85 };
    let currentView = { ...WORLD_VIEW };
    let targetView = { ...WORLD_VIEW };

    let currentMode = 'overview', activeRegion = null;
    let hoveredRegion = -1, hoveredDot = -1;
    let isDragging = false, wasDrag = false;
    let lastMouse = { x: 0, y: 0 }, pinchDist = 0;
    let isVisible = true, time = 0;
    let tooltipEl = null, backBtn = null, regionTitleEl = null;
    let labelEls = [];
    let regionBadgeEls = [];


    function getRegionIdx(lat, lon, countryKey) {
        if (countryKey) {
            for (let i = 0; i < REGIONS.length; i++) {
                const r = REGIONS[i];
                if (!r.countries) continue;
                if (r.countries.indexOf(countryKey) !== -1) return i;
            }
        }
        for (let i = 0; i < REGIONS.length; i++) {
            const r = REGIONS[i];
            if (r.countries) continue;
            if (lat >= r.latMin && lat <= r.latMax && lon >= r.lonMin && lon <= r.lonMax) return i;
        }
        return -1;
    }
    function getRegionDotCount(ri) {
        let c = 0;
        for (let i = 0; i < locationDots.length; i++) if (locationDots[i].regionIdx === ri) c++;
        return c;
    }


    let geoData = null;
    let geoIsHiRes = false;

    function decodeGeo(raw) {
        for (const r of Object.values(raw)) {
            if (!r.polygons) continue;
            for (const poly of r.polygons) {
                const n = poly.lat.length;
                const lat = new Float32Array(n);
                const lon = new Float32Array(n);
                let aLat = 0, aLon = 0;
                for (let i = 0; i < n; i++) {
                    aLat += poly.lat[i];
                    aLon += poly.lon[i];
                    lat[i] = aLat / 1000;
                    lon[i] = aLon / 1000;
                }
                poly.lat = lat;
                poly.lon = lon;
            }
        }
        return raw;
    }

    function upgradeToHiRes() {
        if (geoIsHiRes) return;
        const s = document.createElement('script');
        s.src = (window.ATLAS_URLS && window.ATLAS_URLS.countriesHi) || '/static/js/atlas-countries.js';
        s.async = true;
        s.onload = function () {
            if (typeof atlasCountriesHi === 'undefined') return;
            geoData = decodeGeo(atlasCountriesHi);
            geoIsHiRes = true;
            buildCountryRegionMap();
            buildLocationDots();
            computeRegionStride();
        };
        document.head.appendChild(s);
    }

    function buildCountryRegionMap() {
        countryRegionMap = {};
        polygonRegionMap = {};
        if (!geoData) return;
        for (const [key, r] of Object.entries(geoData)) {
            if (!r.polygons || !r.polygons.length) continue;
            const perPoly = [];
            let biggestIdx = 0, biggestLen = -1;
            for (let i = 0; i < r.polygons.length; i++) {
                const poly = r.polygons[i];
                const cLat = poly.lat.reduce((a, b) => a + b, 0) / poly.lat.length;
                const cLon = poly.lon.reduce((a, b) => a + b, 0) / poly.lon.length;
                perPoly.push(getRegionIdx(cLat, cLon, key));
                if (poly.lat.length > biggestLen) { biggestLen = poly.lat.length; biggestIdx = i; }
            }
            polygonRegionMap[key] = perPoly;
            countryRegionMap[key] = perPoly[biggestIdx];
        }
    }

    function countryTouchesRegion(key, ri) {
        const list = polygonRegionMap[key];
        if (!list) return false;
        for (let i = 0; i < list.length; i++) if (list[i] === ri) return true;
        return false;
    }

    function buildLocationDots() {
        locationDots = [];
        locationCountryMap = {};
        if (typeof atlasLocations === 'undefined' || !geoData) return;
        atlasLocations.forEach((loc, i) => {
            const key = loc.country.toLowerCase().replace(/ /g, '_');
            let lat = 0, lon = 0;
            if (geoData[key] && geoData[key].polygons && geoData[key].polygons.length) {
                const main = geoData[key].polygons[0];
                lat = main.lat.reduce((a, b) => a + b, 0) / main.lat.length;
                lon = main.lon.reduce((a, b) => a + b, 0) / main.lon.length;
            }
            locationDots.push({ lat, lon, locIdx: i, regionIdx: getRegionIdx(lat, lon, key), countryKey: key });
            locationCountryMap[key] = i;
        });
    }


    function lonToX(lon) {
        return (lon - currentView.lonMin) / (currentView.lonMax - currentView.lonMin) * canvas.width;
    }
    function latToY(lat) {
        return (1 - (lat - currentView.latMin) / (currentView.latMax - currentView.latMin)) * canvas.height;
    }
    function screenToLatLon(px, py) {
        return {
            lon: (px / canvas.width) * (currentView.lonMax - currentView.lonMin) + currentView.lonMin,
            lat: (1 - py / canvas.height) * (currentView.latMax - currentView.latMin) + currentView.latMin
        };
    }


    function pointInPolygon(lat, lon, poly) {
        const plat = poly.lat, plon = poly.lon;
        let inside = false;
        for (let i = 0, j = plat.length - 1; i < plat.length; j = i++) {
            const yi = plat[i], yj = plat[j];
            const xi = plon[i], xj = plon[j];
            if ((yi > lat) !== (yj > lat) && lon < (xj - xi) * (lat - yi) / (yj - yi) + xi) {
                inside = !inside;
            }
        }
        return inside;
    }

    function findRegionAt(px, py) {
        const { lat, lon } = screenToLatLon(px, py);

        if (geoData) {
            for (const key of Object.keys(geoData)) {
                const r = geoData[key];
                if (!r.polygons || !r.polygons.length) continue;
                const regions = polygonRegionMap[key];
                if (!regions) continue;
                for (let pi = 0; pi < r.polygons.length; pi++) {
                    const ri = regions[pi];
                    if (ri < 0 || getRegionDotCount(ri) === 0) continue;
                    if (pointInPolygon(lat, lon, r.polygons[pi])) return ri;
                }
            }
        }

        for (let i = 0; i < REGIONS.length; i++) {
            const r = REGIONS[i];
            if (r.countries) continue;
            if (lat >= r.latMin && lat <= r.latMax && lon >= r.lonMin && lon <= r.lonMax && getRegionDotCount(i) > 0) return i;
        }
        return -1;
    }
    function findDotAt(px, py) {
        if (currentMode !== 'region') return -1;
        const hitRadius = isMobile ? 44 : 28;
        for (let i = 0; i < locationDots.length; i++) {
            const d = locationDots[i];
            if (d.regionIdx !== activeRegion) continue;
            const sx = lonToX(d.lon), sy = latToY(d.lat);
            if (Math.hypot(sx - px, sy - py) < hitRadius) return i;
        }
        return -1;
    }
    function findCountryAt(px, py) {
        const { lat, lon } = screenToLatLon(px, py);
        for (const [key, r] of Object.entries(geoData)) {
            if (!r.polygons || !r.polygons.length) continue;
            if (currentMode === 'region') {
                if (!countryTouchesRegion(key, activeRegion)) continue;
            }
            if (!locationCountryMap.hasOwnProperty(key)) continue;
            let inside = false;
            for (const poly of r.polygons) {
                const plat = poly.lat, plon = poly.lon;
                for (let i = 0, j = plat.length - 1; i < plat.length; j = i++) {
                    const yi = plat[i], yj = plat[j];
                    const xi = plon[i], xj = plon[j];
                    if ((yi > lat) !== (yj > lat) && lon < (xj - xi) * (lat - yi) / (yj - yi) + xi) {
                        inside = !inside;
                    }
                }
            }
            if (inside) return key;
        }
        return null;
    }


    function keyPhase(key) {
        let h = 0;
        for (let i = 0; i < key.length; i++) h = (h * 31 + key.charCodeAt(i)) % 1000;
        return (h / 1000) * Math.PI * 2;
    }

    const REGION_POINT_BUDGET = 7000;
    let regionStrideBase = 1;

    function computeRegionStride() {
        regionStrideBase = 1;
        if (currentMode !== 'region' || activeRegion === null || !geoData) return;
        let pts = 0;
        for (const key of Object.keys(geoData)) {
            if (!countryTouchesRegion(key, activeRegion)) continue;
            const r = geoData[key];
            if (!r.polygons) continue;
            for (const poly of r.polygons) pts += poly.lat.length;
        }
        regionStrideBase = Math.max(1, Math.min(8, Math.ceil(pts / REGION_POINT_BUDGET)));
    }

    function strideForLonSpan(lonSpan) {
        if (currentMode !== 'region') return 10;
        const zoomRelief = Math.max(1, Math.min(4, 140 / Math.max(lonSpan, 1)));
        return Math.max(1, Math.round(regionStrideBase / zoomRelief));
    }

    function tracePath(lats, lons, stride, offsetX, offsetY) {
        const n = lats.length;
        const st = stride || 1;
        const ox = offsetX || 0, oy = offsetY || 0;
        let started = false;
        for (let i = 0; i < n; i += st) {
            const x = lonToX(lons[i]) + ox;
            const y = latToY(lats[i]) + oy;
            if (!started) { ctx.moveTo(x, y); started = true; }
            else ctx.lineTo(x, y);
        }
        if (started && (n - 1) % st !== 0) {
            const last = n - 1;
            ctx.lineTo(lonToX(lons[last]) + ox, latToY(lats[last]) + oy);
        }
    }

    function drawCountryPath(r, stride, key, regionFilter, invert) {
        const regions = (regionFilter === undefined || regionFilter === null)
            ? null : polygonRegionMap[key];
        ctx.beginPath();
        for (let i = 0; i < r.polygons.length; i++) {
            if (regions) {
                const inRegion = regions[i] === regionFilter;
                if (invert ? inRegion : !inRegion) continue;
            }
            const poly = r.polygons[i];
            tracePath(poly.lat, poly.lon, stride);
            ctx.closePath();
        }
    }


    function borderVibration(phase) {
        const vx = Math.sin(time * 2.6 + phase) * 0.5 + Math.sin(time * 5.1 + phase * 1.7) * 0.25;
        const vy = Math.cos(time * 2.3 + phase * 1.3) * 0.5 + Math.cos(time * 4.7 + phase * 0.9) * 0.25;
        return { vx, vy };
    }

    function drawDetailedBorder(r, isDark, isActive, height, stride, phase) {
        const h = height || 0.5;
        const v = borderVibration(phase || 0);
        ctx.save();
        ctx.translate(v.vx, v.vy);
        drawCountryPath(r, stride);

        if (isActive) {
            const borderA = 0.2 + h * 0.15;
            ctx.strokeStyle = isDark ? 'rgba(255,255,255,' + borderA.toFixed(2) + ')' : 'rgba(0,0,0,' + (borderA * 0.85).toFixed(2) + ')';
            ctx.lineWidth = isMobile ? 1.0 : 0.8;
        } else {
            const borderA = 0.04 + h * 0.06;
            ctx.strokeStyle = isDark ? 'rgba(255,255,255,' + borderA.toFixed(2) + ')' : 'rgba(0,0,0,' + (borderA * 0.7).toFixed(2) + ')';
            ctx.lineWidth = isMobile ? 0.6 : 0.4;
        }
        ctx.stroke();

        if (isActive) {
            drawCountryPath(r, stride);
            ctx.strokeStyle = isDark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.03)';
            ctx.lineWidth = 2.5;
            ctx.stroke();
        }
        ctx.restore();
    }


    function getCountriesInRegion(ri) {
        const regionCountries = new Set();
        for (let i = 0; i < locationDots.length; i++) {
            if (locationDots[i].regionIdx === ri) regionCountries.add(locationDots[i].countryKey);
        }
        return regionCountries;
    }


    function computeRegionBounds(ri) {
        const regionCountries = getCountriesInRegion(ri);
        let latMin = 90, latMax = -90, lonMin = 180, lonMax = -180;
        for (const key of regionCountries) {
            if (!geoData[key] || !geoData[key].polygons || !geoData[key].polygons.length) continue;
            const main = geoData[key].polygons[0];
            for (let i = 0; i < main.lat.length; i++) {
                if (main.lat[i] < latMin) latMin = main.lat[i];
                if (main.lat[i] > latMax) latMax = main.lat[i];
                if (main.lon[i] < lonMin) lonMin = main.lon[i];
                if (main.lon[i] > lonMax) lonMax = main.lon[i];
            }
        }
        if (latMin >= latMax) {
            const reg = REGIONS[ri];
            return { latMin: reg.latMin, latMax: reg.latMax, lonMin: reg.lonMin, lonMax: reg.lonMax };
        }
        return { latMin, latMax, lonMin, lonMax };
    }


    function enterRegion(ri) {
        if (getRegionDotCount(ri) === 0) return;
        currentMode = 'region'; activeRegion = ri; hoveredRegion = -1; hoveredDot = -1;
        computeRegionStride();
        const bounds = computeRegionBounds(ri);
        const pad = isMobile ? 8 : 5;
        const asp = canvas.width / canvas.height;
        let lonSpan = (bounds.lonMax - bounds.lonMin) + pad * 2;
        let latSpan = lonSpan / asp;
        const latC = (bounds.latMin + bounds.latMax) / 2;
        const lonC = (bounds.lonMin + bounds.lonMax) / 2;
        const minLat = (bounds.latMax - bounds.latMin) + pad * 2;
        if (latSpan < minLat) { latSpan = minLat; lonSpan = latSpan * asp; }
        targetView = { lonMin: lonC - lonSpan / 2, lonMax: lonC + lonSpan / 2, latMin: latC - latSpan / 2, latMax: latC + latSpan / 2 };
    }
    function exitRegion() {
        currentMode = 'overview'; activeRegion = null; hoveredDot = -1; hoveredRegion = -1;
        WORLD_VIEW = computeWorldView(); targetView = { ...WORLD_VIEW };
    }


    function zoomAround(lat, lon, factor) {
        const curLon = targetView.lonMax - targetView.lonMin;
        const curLat = targetView.latMax - targetView.latMin;
        let nextLon = curLon * factor;
        if (nextLon < MIN_LON_SPAN) nextLon = MIN_LON_SPAN;
        if (nextLon > MAX_LON_SPAN) nextLon = MAX_LON_SPAN;
        const applied = nextLon / curLon;
        if (applied === 1) return;
        const nextLat = curLat * applied;

        const fx = (lon - targetView.lonMin) / curLon;
        const fy = (lat - targetView.latMin) / curLat;

        targetView.lonMin = lon - nextLon * fx;
        targetView.lonMax = targetView.lonMin + nextLon;
        targetView.latMin = lat - nextLat * fy;
        targetView.latMax = targetView.latMin + nextLat;
    }

    function setupInteraction() {
        canvas.addEventListener('contextmenu', e => {
            e.preventDefault();
            if (currentMode === 'region') exitRegion();
        });
        canvas.addEventListener('mousedown', e => { if (e.button !== 0) return; isDragging = true; wasDrag = false; lastMouse = { x: e.clientX, y: e.clientY }; });
        window.addEventListener('mousemove', e => {
            const rect = canvas.getBoundingClientRect();
            const dpr = canvas.width / rect.width;
            const px = (e.clientX - rect.left) * dpr, py = (e.clientY - rect.top) * dpr;
            if (currentMode === 'overview') {
                hoveredDot = -1;
                hoveredRegion = findRegionAt(px, py);
                if (!isDragging) canvas.style.cursor = hoveredRegion >= 0 ? 'pointer' : 'default';
            } else {
                hoveredDot = findDotAt(px, py);
                if (!isDragging) {
                    if (hoveredDot >= 0) { canvas.style.cursor = 'pointer'; }
                    else { canvas.style.cursor = findCountryAt(px, py) ? 'pointer' : 'default'; }
                }
            }
            if (tooltipEl) {
                tooltipEl.style.left = (e.clientX - rect.left) + 'px';
                tooltipEl.style.top = (e.clientY - rect.top - 50) + 'px';
            }
            if (!isDragging) return;
            const dx = e.clientX - lastMouse.x, dy = e.clientY - lastMouse.y;
            if (Math.abs(dx) > 2 || Math.abs(dy) > 2) wasDrag = true;
            if (wasDrag) {
                const lonSpan = currentView.lonMax - currentView.lonMin;
                const latSpan = currentView.latMax - currentView.latMin;
                targetView.lonMin += -dx / rect.width * lonSpan * DRAG_SCALE;
                targetView.lonMax += -dx / rect.width * lonSpan * DRAG_SCALE;
                targetView.latMin += dy / rect.height * latSpan * DRAG_SCALE;
                targetView.latMax += dy / rect.height * latSpan * DRAG_SCALE;
                canvas.style.cursor = 'grabbing';
            }
            lastMouse = { x: e.clientX, y: e.clientY };
        });
        window.addEventListener('mouseup', e => {
            if (isDragging && !wasDrag) handleClick(e);
            isDragging = false;
            if (currentMode === 'overview') canvas.style.cursor = hoveredRegion >= 0 ? 'pointer' : 'default';
            else canvas.style.cursor = (hoveredDot >= 0) ? 'pointer' : 'default';
        });

        canvas.addEventListener('wheel', e => {
            e.preventDefault();
            const factor = e.deltaY > 0 ? ZOOM_FACTOR_OUT : ZOOM_FACTOR_IN;
            const rect = canvas.getBoundingClientRect();
            const dpr = canvas.width / rect.width;
            const { lat, lon } = screenToLatLon((e.clientX - rect.left) * dpr, (e.clientY - rect.top) * dpr);
            zoomAround(lat, lon, factor);
        }, { passive: false });

        canvas.addEventListener('touchstart', e => {
            e.preventDefault();
            if (e.touches.length === 2) {
                const dx = e.touches[0].clientX - e.touches[1].clientX;
                const dy = e.touches[0].clientY - e.touches[1].clientY;
                pinchDist = Math.hypot(dx, dy);
                isDragging = false;
                return;
            }
            if (e.touches.length === 1) {
                isDragging = true; wasDrag = false;
                lastMouse = { x: e.touches[0].clientX, y: e.touches[0].clientY };
                const rect = canvas.getBoundingClientRect(), dpr = canvas.width / rect.width;
                hoveredDot = findDotAt((e.touches[0].clientX - rect.left) * dpr, (e.touches[0].clientY - rect.top) * dpr);
            }
        }, { passive: false });
        canvas.addEventListener('touchmove', e => {
            e.preventDefault();
            if (e.touches.length === 1 && isDragging) {
                const dx = e.touches[0].clientX - lastMouse.x, dy = e.touches[0].clientY - lastMouse.y;
                if (Math.abs(dx) > 2 || Math.abs(dy) > 2) wasDrag = true;
                if (wasDrag) {
                    const rect = canvas.getBoundingClientRect();
                    const lonSpan = currentView.lonMax - currentView.lonMin, latSpan = currentView.latMax - currentView.latMin;
                    targetView.lonMin += -dx / rect.width * lonSpan * TOUCH_DRAG_SCALE;
                    targetView.lonMax += -dx / rect.width * lonSpan * TOUCH_DRAG_SCALE;
                    targetView.latMin += dy / rect.height * latSpan * TOUCH_DRAG_SCALE;
                    targetView.latMax += dy / rect.height * latSpan * TOUCH_DRAG_SCALE;
                }
                lastMouse = { x: e.touches[0].clientX, y: e.touches[0].clientY };
            } else if (e.touches.length === 2 && pinchDist > 0) {
                const dx = e.touches[0].clientX - e.touches[1].clientX;
                const dy = e.touches[0].clientY - e.touches[1].clientY;
                const dist = Math.hypot(dx, dy);
                if (dist > 0) {
                    const rect = canvas.getBoundingClientRect();
                    const dpr = canvas.width / rect.width;
                    const mx = (e.touches[0].clientX + e.touches[1].clientX) / 2;
                    const my = (e.touches[0].clientY + e.touches[1].clientY) / 2;
                    const { lat, lon } = screenToLatLon((mx - rect.left) * dpr, (my - rect.top) * dpr);
                    zoomAround(lat, lon, pinchDist / dist);
                    pinchDist = dist;
                }
            }
        }, { passive: false });
        canvas.addEventListener('touchend', e => {
            if (e.touches.length < 2) pinchDist = 0;
            if (isDragging && !wasDrag && e.changedTouches && e.changedTouches.length === 1)
                handleClick(e.changedTouches[0]);
            isDragging = false; hoveredDot = -1;
        }, { passive: true });
    }

    function handleClick(e) {
        if (e.button && e.button !== 0) return;
        const rect = canvas.getBoundingClientRect(), dpr = canvas.width / rect.width;
        const px = (e.clientX - rect.left) * dpr, py = (e.clientY - rect.top) * dpr;
        if (currentMode === 'region') {
            const di = findDotAt(px, py);
            if (di >= 0) {
                const loc = atlasLocations[locationDots[di].locIdx];
                window.location.href = loc.url || ('/atlas/' + loc.internal_id);
                return;
            }
            const countryKey = findCountryAt(px, py);
            if (countryKey && locationCountryMap.hasOwnProperty(countryKey)) {
                const locIdx = locationCountryMap[countryKey];
                const loc = atlasLocations[locIdx];
                window.location.href = loc.url || ('/atlas/' + loc.internal_id);
                return;
            }
        } else {
            const ri = findRegionAt(px, py);
            if (ri >= 0) enterRegion(ri);
        }
    }


    function createUI() {
        const container = document.getElementById('flatearththeory');
        if (!container) return;

        tooltipEl = document.createElement('div');
        tooltipEl.id = 'unsolicitedinfo';
        tooltipEl.style.cssText = 'position:absolute;pointer-events:none;opacity:0;transition:opacity 0.15s;white-space:nowrap;transform:translate(-50%,0);z-index:20;';
        container.appendChild(tooltipEl);

        backBtn = document.createElement('button');
        backBtn.className = 'retreatbutton';
        backBtn.innerHTML = '<img src="/static/images/entities/notok.svg" alt="Close" style="width:14px;height:14px;display:block;">';
        backBtn.style.cssText = 'position:absolute;top:5rem;left:1.5rem;pointer-events:auto;z-index:30;display:none;align-items:center;justify-content:center;width:36px;height:36px;padding:0;background:rgba(244,244,244,0.6);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);border:1px solid rgba(21,22,23,0.1);border-radius:0;cursor:pointer;transition:opacity 0.3s;';
        backBtn.addEventListener('click', exitRegion);
        container.appendChild(backBtn);

        regionTitleEl = document.createElement('div');
        regionTitleEl.id = 'whereamiexactly';
        regionTitleEl.style.cssText = 'position:absolute;top:5rem;left:50%;transform:translateX(-50%);pointer-events:none;z-index:25;font-family:var(--font-family,monospace);font-size:' + (isMobile ? '0.8rem' : '1rem') + ';font-weight:900;letter-spacing:0.1em;text-transform:uppercase;color:var(--color-text,#000);opacity:0;transition:opacity 0.4s;white-space:nowrap;';
        container.appendChild(regionTitleEl);


        for (let i = 0; i < REGIONS.length; i++) {
            const count = getRegionDotCount(i);
            if (count === 0) { regionBadgeEls.push(null); continue; }
            const el = document.createElement('div');
            el.className = 'howmanystamps';
            el.style.cssText = 'position:absolute;pointer-events:auto;cursor:pointer;z-index:16;opacity:0;transition:opacity 0.3s,transform 0.2s;white-space:nowrap;transform:translate(-50%,-50%);display:flex;align-items:center;gap:4px;';
            el.innerHTML = '<span class="thetally">' + count + ' LOC' + (count > 1 ? 'S' : '') + '</span>';
            el.setAttribute('data-region', i);
            el.addEventListener('click', (function(ri) { return function(e) { e.stopPropagation(); enterRegion(ri); }; })(i));
            container.appendChild(el);
            regionBadgeEls.push(el);
        }


        if (typeof atlasLocations !== 'undefined') {
            atlasLocations.forEach((loc, i) => {
                const el = document.createElement('a');
                el.href = loc.url || ('/atlas/' + loc.internal_id);
                el.className = 'pindrop';
                el.style.cssText = 'position:absolute;pointer-events:none;text-decoration:none;color:var(--color-text,#000);opacity:0;transition:opacity 0.4s;white-space:nowrap;transform:translate(-50%,0);display:flex;flex-direction:column;align-items:center;gap:1px;';
                el.innerHTML = '<span class="pindropnumber">' + loc.internal_id + '</span><span class="pindropname">' + loc.country + '</span>';
                container.appendChild(el);
                labelEls.push(el);
            });
        }
    }


    function drawCoordinateGrid(w, h, isDark) {
        const alpha = isDark ? 0.025 : 0.018;
        ctx.strokeStyle = isDark ? 'rgba(255,255,255,' + alpha + ')' : 'rgba(0,0,0,' + alpha + ')';
        ctx.lineWidth = 0.5;
        ctx.setLineDash([4, 8]);
        for (let lon = -180; lon <= 180; lon += 30) {
            const x = lonToX(lon);
            if (x < -1 || x > w + 1) continue;
            ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
        }
        for (let lat = -90; lat <= 90; lat += 30) {
            const y = latToY(lat);
            if (y < -1 || y > h + 1) continue;
            ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
        }
        ctx.setLineDash([]);
    }


    let terrainImg = null, terrainReady = false;

    function initTerrainImage() {
        if (terrainImg) return;
        terrainImg = new Image();
        terrainImg.onload = function () { terrainReady = true; };
        terrainImg.onerror = function () { terrainReady = false; };
        terrainImg.src = (window.ATLAS_URLS && window.ATLAS_URLS.terrain) || '/static/images/atlas-terrain.png';
    }

    function drawTerrainBackdrop(isDark) {
        if (!terrainReady || typeof atlasTerrainMeta === 'undefined') return;
        const meta = atlasTerrainMeta;

        const lonA = Math.max(meta.lonMin, currentView.lonMin);
        const lonB = Math.min(meta.lonMax, currentView.lonMax);
        const latA = Math.max(meta.latMin, currentView.latMin);
        const latB = Math.min(meta.latMax, currentView.latMax);
        if (lonB <= lonA || latB <= latA) return;

        const sx = (lonA - meta.lonMin) / (meta.lonMax - meta.lonMin) * meta.width;
        const sw = (lonB - lonA) / (meta.lonMax - meta.lonMin) * meta.width;
        const sy = (meta.latMax - latB) / (meta.latMax - meta.latMin) * meta.height;
        const sh = (latB - latA) / (meta.latMax - meta.latMin) * meta.height;
        if (sw < 1 || sh < 1) return;

        const dx = lonToX(lonA), dy = latToY(latB);
        const dw = lonToX(lonB) - dx, dh = latToY(latA) - dy;
        if (dw <= 0 || dh <= 0) return;

        ctx.save();

        if (isDark) ctx.filter = 'invert(1)';
        ctx.imageSmoothingEnabled = true;
        if (ctx.imageSmoothingQuality) ctx.imageSmoothingQuality = 'high';
        ctx.drawImage(terrainImg, sx, sy, sw, sh, dx, dy, dw, dh);
        if (isDark) ctx.filter = 'none';

        ctx.restore();
    }


    function drawLocationMarkers(isDark) {
        if (currentMode !== 'region') return;

        const dpr = canvas.width / (parseFloat(canvas.style.width) || window.innerWidth);
        const side = MARKER_SIZE * dpr;
        const ink = isDark ? '255,255,255' : '0,0,0';

        for (let i = 0; i < locationDots.length; i++) {
            const d = locationDots[i];
            if (d.regionIdx !== activeRegion) continue;

            const x = lonToX(d.lon), y = latToY(d.lat);
            if (x < -40 || x > canvas.width + 40 || y < -40 || y > canvas.height + 40) continue;

            const isHov = hoveredDot === i;
            const half = (isHov ? side * 1.3 : side) / 2;

            ctx.fillStyle = 'rgba(' + ink + ',' + (isHov ? 1 : 0.8) + ')';
            ctx.fillRect(x - half, y - half, half * 2, half * 2);
        }
    }

    function drawCountryHatching(r, isDark, spacing, stride, key, regionFilter) {
        const regions = (regionFilter === undefined || regionFilter === null)
            ? null : polygonRegionMap[key];
        ctx.save();
        drawCountryPath(r, stride, key, regionFilter);
        ctx.clip();
        let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
        for (let pi = 0; pi < r.polygons.length; pi++) {
            if (regions && regions[pi] !== regionFilter) continue;
            const poly = r.polygons[pi];
            for (let i = 0; i < poly.lat.length; i += (stride || 1)) {
                const x = lonToX(poly.lon[i]), y = latToY(poly.lat[i]);
                if (x < minX) minX = x; if (x > maxX) maxX = x;
                if (y < minY) minY = y; if (y > maxY) maxY = y;
            }
        }
        const alpha = isDark ? 0.06 : 0.04;
        ctx.strokeStyle = isDark ? 'rgba(255,255,255,' + alpha + ')' : 'rgba(0,0,0,' + alpha + ')';
        ctx.lineWidth = 0.4;
        ctx.setLineDash([2, 4]);
        const sp = spacing || 8;
        const range = maxX - minX + maxY - minY;
        ctx.beginPath();
        for (let d = 0; d < range; d += sp) {
            const x1 = minX + d, y1 = minY;
            const x2 = minX, y2 = minY + d;
            ctx.moveTo(x1, y1); ctx.lineTo(x2, y2);
        }
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.restore();
    }


    /* Frame budget from the shared tier — see js/howfastareyou.js. */
    const ATLAS_FRAME_MS = (window.WiehrTier && window.WiehrTier.fps)
        ? 1000 / window.WiehrTier.fps - 4 : 0;   // -4: see frame() in howfastareyou.js
    let atlasLastFrameAt = 0;

    function render(now) {
        if (!isVisible) { requestAnimationFrame(render); return; }

        if (ATLAS_FRAME_MS) {
            if (now - atlasLastFrameAt < ATLAS_FRAME_MS) { requestAnimationFrame(render); return; }
            atlasLastFrameAt = now;
        }

        time += 0.016;

        currentView.lonMin += (targetView.lonMin - currentView.lonMin) * LERP_SPEED;
        currentView.lonMax += (targetView.lonMax - currentView.lonMax) * LERP_SPEED;
        currentView.latMin += (targetView.latMin - currentView.latMin) * LERP_SPEED;
        currentView.latMax += (targetView.latMax - currentView.latMax) * LERP_SPEED;

        const isDark = document.documentElement.getAttribute('data-wiehr-theme') === 'dark';
        const w = canvas.width, h = canvas.height;


        ctx.clearRect(0, 0, w, h);

        drawCoordinateGrid(w, h, isDark);

        const lonSpan = currentView.lonMax - currentView.lonMin;
        const stride = strideForLonSpan(lonSpan);

        drawTerrainBackdrop(isDark);

        if (geoData) {
            const highlightCountries = new Set();
            const activeCountries = new Set();
            const regionCountriesSet = new Set();
            if (currentMode === 'overview' && hoveredRegion >= 0) {
                for (const key of Object.keys(polygonRegionMap)) {
                    if (countryTouchesRegion(key, hoveredRegion)) highlightCountries.add(key);
                }
            }
            if (currentMode === 'region' && activeRegion !== null) {
                for (let i = 0; i < locationDots.length; i++) {
                    if (locationDots[i].regionIdx === activeRegion) activeCountries.add(locationDots[i].countryKey);
                }
                for (const key of Object.keys(polygonRegionMap)) {
                    if (countryTouchesRegion(key, activeRegion)) regionCountriesSet.add(key);
                }
            }


            for (const [key, r] of Object.entries(geoData)) {
                if (!r.polygons || !r.polygons.length) continue;
                if (currentMode === 'region' && !regionCountriesSet.has(key)) continue;

                const isHighlighted = highlightCountries.has(key);
                const isActive = activeCountries.has(key);
                const hasLocation = locationCountryMap.hasOwnProperty(key);

                const maskStyle = (isActive || hasLocation)
                    ? (isDark ? 'rgba(21,22,23,0.72)' : 'rgba(255,255,255,0.72)')
                    : (isDark ? 'rgba(21,22,23,0.55)' : 'rgba(255,255,255,0.55)');

                if (isHighlighted) {
                    ctx.fillStyle = maskStyle;
                    drawCountryPath(r, stride, key, hoveredRegion, true);
                    ctx.fill();
                } else {
                    ctx.fillStyle = maskStyle;
                    drawCountryPath(r, stride, key, null);
                    ctx.fill();
                }
            }


            for (const [key, r] of Object.entries(geoData)) {
                if (!r.polygons || !r.polygons.length) continue;
                if (currentMode === 'region' && !regionCountriesSet.has(key)) continue;
                if (!locationCountryMap.hasOwnProperty(key)) continue;
                const isHighlighted = highlightCountries.has(key);
                const isActive = activeCountries.has(key);
                if (isHighlighted || isActive) {
                    const hatchFilter = isHighlighted ? hoveredRegion
                        : (currentMode === 'region' ? activeRegion : null);
                    const hatchSpacing = Math.max(4, Math.min(10, lonSpan / 35)) * regionStrideBase;
                    drawCountryHatching(r, isDark, hatchSpacing, stride, key, hatchFilter);
                }
            }


            for (const [key, r] of Object.entries(geoData)) {
                if (!r.polygons || !r.polygons.length) continue;
                if (currentMode === 'region' && !regionCountriesSet.has(key)) continue;
                const isHighlighted = highlightCountries.has(key);
                const isActive = activeCountries.has(key);
                drawDetailedBorder(r, isDark, isHighlighted || isActive, r.height || 0.5, stride, keyPhase(key));
            }
        }

        drawLocationMarkers(isDark);


        const dpr = canvas.width / (parseFloat(canvas.style.width) || window.innerWidth);


        for (let i = 0; i < regionBadgeEls.length; i++) {
            const el = regionBadgeEls[i];
            if (!el) continue;
            if (currentMode !== 'overview') {
                el.style.opacity = '0'; el.style.pointerEvents = 'none'; continue;
            }
            const r = REGIONS[i];
            const cLat = (r.latMin + r.latMax) / 2;
            const cLon = (r.lonMin + r.lonMax) / 2;
            const sx = lonToX(cLon) / dpr, sy = latToY(cLat) / dpr;
            if (sx < -80 || sx > window.innerWidth + 80 || sy < -50 || sy > window.innerHeight + 50) {
                el.style.opacity = '0'; el.style.pointerEvents = 'none'; continue;
            }
            el.style.left = sx + 'px';
            el.style.top = sy + 'px';
            const isHov = hoveredRegion === i;
            el.style.opacity = isHov ? '1' : '0.7';
            el.style.transform = isHov ? 'translate(-50%,-50%) scale(1.1)' : 'translate(-50%,-50%)';
            el.style.pointerEvents = 'auto';
        }


        const labelOffset = MARKER_SIZE * 1.3 + 14;

        for (let i = 0; i < labelEls.length; i++) {
            const el = labelEls[i];
            const d = locationDots[i];

            if (currentMode !== 'region' || d.regionIdx !== activeRegion) {
                el.style.opacity = '0'; el.style.pointerEvents = 'none'; continue;
            }

            const sx = lonToX(d.lon) / dpr, sy = latToY(d.lat) / dpr;
            if (sx < -50 || sx > window.innerWidth + 50 || sy < -50 || sy > window.innerHeight + 50) {
                el.style.opacity = '0'; el.style.pointerEvents = 'none'; continue;
            }
            el.style.left = sx + 'px';
            el.style.top = (sy + labelOffset) + 'px';
            const isHov = hoveredDot === i;
            el.classList.toggle('hovered', isHov);
            el.style.opacity = isHov ? '1' : '0.85';
            el.style.pointerEvents = 'auto';
        }


        if (tooltipEl) {
            if (hoveredDot >= 0 && currentMode === 'region') {
                const loc = atlasLocations[locationDots[hoveredDot].locIdx];
                tooltipEl.innerHTML = '<span class="receiptnumber">' + loc.internal_id + '</span><span class="thedivider">//</span><span class="theactualplace">' + loc.country + '</span>';
                tooltipEl.style.opacity = '1';
            } else {
                tooltipEl.style.opacity = '0';
            }
        }
        if (backBtn) backBtn.style.display = currentMode === 'region' ? 'flex' : 'none';
        if (regionTitleEl) {
            if (currentMode === 'region' && activeRegion !== null) {
                regionTitleEl.textContent = REGIONS[activeRegion].name;
                regionTitleEl.style.opacity = '1';
            } else { regionTitleEl.style.opacity = '0'; }
        }

        requestAnimationFrame(render);
    }


    let resizeTimer = null;
    function updateCanvasSize() {
        const dpr = Math.min(window.devicePixelRatio || 1, isMobile ? 1.5 : 2);
        const w = Math.round(window.innerWidth * dpr);
        const h = Math.round(window.innerHeight * dpr);
        if (canvas.width !== w || canvas.height !== h) {
            canvas.width = w;
            canvas.height = h;
        }
        canvas.style.width = window.innerWidth + 'px';
        canvas.style.height = window.innerHeight + 'px';
    }

    function resize() {
        updateCanvasSize();
        WORLD_VIEW = computeWorldView();
        if (currentMode === 'overview') targetView = { ...WORLD_VIEW };
    }

    function onResize() {

        canvas.style.width = window.innerWidth + 'px';
        canvas.style.height = window.innerHeight + 'px';

        if (resizeTimer) clearTimeout(resizeTimer);
        resizeTimer = setTimeout(resize, 100);
    }

    function init() {
        canvas = document.getElementById('tracingmysteps');
        if (!canvas) return false;
        ctx = canvas.getContext('2d');
        if (!ctx) return false;
        updateCanvasSize();
        WORLD_VIEW = computeWorldView();
        currentView = { ...WORLD_VIEW }; targetView = { ...WORLD_VIEW };
        window.addEventListener('resize', onResize);
        return true;
    }

    function start() {
        if (typeof atlasCountriesLo !== 'undefined') {
            geoData = decodeGeo(atlasCountriesLo);
            buildCountryRegionMap();
            buildLocationDots();
            createUI();
            setupInteraction();
            render();
            window.atlasInitialized = true;

            upgradeToHiRes();
            initTerrainImage();
        } else { setTimeout(start, 100); }
    }

    document.addEventListener('keydown', e => { if (e.key === 'Escape' && currentMode === 'region') exitRegion(); });
    window.pauseWebGL = () => { isVisible = false; };
    window.resumeWebGL = () => { isVisible = true; };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => { if (init()) start(); });
    } else { if (init()) start(); }
    document.addEventListener('visibilitychange', () => { isVisible = !document.hidden; });
})();
