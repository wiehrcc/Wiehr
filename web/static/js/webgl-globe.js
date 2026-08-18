
(function() {
    'use strict';

    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) || window.innerWidth <= 640;
    const isLowPerf = (window.WIEHR_PERFORMANCE || (isMobile ? 'low' : 'high')) === 'low';


    const GRID_COLS = isLowPerf ? 180 : 300;
    const GRID_ROWS = isLowPerf ? 90 : 150;
    const OCEAN_COLS = isLowPerf ? 120 : 220;
    const OCEAN_ROWS = isLowPerf ? 60 : 110;
    const NOISE_COUNT = isLowPerf ? 200 : 400;
    const POINT_SIZE = isLowPerf ? 2.0 : 2.5;
    const CUBE_SIZE = isLowPerf ? 28.0 : 38.0;
    const GLOBE_RADIUS = 0.45;

    const ZOOM_MIN = isLowPerf ? 0.6 : 0.4;    
    const ZOOM_MAX = isLowPerf ? 3.5 : 3.0;      
    const ZOOM_DEFAULT = isMobile ? (isLowPerf ? 2.4 : 2.0) : (isLowPerf ? 1.6 : 1.4);
    const BELARUS = { lat: 53.8875, lon: 25.2997 }; 

    let canvas, gl;
    let landProgram, oceanProgram, noiseProgram, cubeProgram, lineProgram;
    let landVAO, oceanVAO, noiseVAO, cubeVAO, lineVAO, belarusVAO;
    let landBuffer, oceanBuffer, noiseBuffer, cubeBuffer, lineBuffer, belarusBuffer;

    let landPoints = [];
    let oceanPoints = [];
    let noiseParticles = [];
    let landData, oceanData, noiseData;
    let dotPositions = [];
    let dotColors = [];
    let dotData = [];
    let lineData = [];

    let belarusBorder = [];
    let mapCanvas, mapCtx;
    let rotation = { x: isMobile ? 0.25 : 0.4, y: 0.0 };
    let targetRotation = { x: isMobile ? 0.25 : 0.4, y: 0.0 };
    let autoRotate = true;
    let zoom = ZOOM_DEFAULT;
    let targetZoom = ZOOM_DEFAULT;
    let time = 0;
    let isDragging = false;
    let wasDrag = false;
    let lastMouse = { x: 0, y: 0 };
    let pinchDist = 0;
    let isVisible = true;
    let hoveredDot = -1;


    const TILT_LIMIT = Math.PI / 2 - 0.09;

    function clampTilt(value) {
        return Math.max(-TILT_LIMIT, Math.min(TILT_LIMIT, value));
    }


    const landVS = `#version 300 es
        precision highp float;
        in vec3 aPosition;
        in float aDepth;
        out float vDepth;
        uniform float uPointSize;
        void main() {
            gl_Position = vec4(aPosition.xy, 0.0, 1.0);
            gl_PointSize = uPointSize * (0.8 + aDepth * 0.4);
            vDepth = aDepth;
        }
    `;

    const landFS = `#version 300 es
        precision highp float;
        in float vDepth;
        out vec4 fragColor;
        uniform float uIsDark;
        void main() {
            vec2 c = gl_PointCoord - 0.5;
            if (length(c) > 0.45) discard;
            float gray = mix(0.0 + vDepth * 0.1, 0.9 + vDepth * 0.1, uIsDark);
            fragColor = vec4(gray, gray, gray, 1.0);
        }
    `;


    const oceanVS = `#version 300 es
        precision highp float;
        in vec3 aPosition;
        in float aAlpha;
        out float vAlpha;
        uniform float uPointSize;
        void main() {
            gl_Position = vec4(aPosition.xy, 0.0, 1.0);
            gl_PointSize = uPointSize * 0.6;
            vAlpha = aAlpha;
        }
    `;

    const oceanFS = `#version 300 es
        precision highp float;
        in float vAlpha;
        out vec4 fragColor;
        uniform float uIsDark;
        void main() {
            vec2 c = gl_PointCoord - 0.5;
            if (length(c) > 0.5) discard;
            float gray = mix(0.3, 0.7, uIsDark);
            fragColor = vec4(gray, gray, gray, vAlpha);
        }
    `;


    const noiseVS = `#version 300 es
        precision highp float;
        in vec2 aPosition;
        in float aSize;
        in float aAlpha;
        out float vAlpha;
        void main() {
            gl_Position = vec4(aPosition, 0.0, 1.0);
            gl_PointSize = aSize;
            vAlpha = aAlpha;
        }
    `;

    const noiseFS = `#version 300 es
        precision highp float;
        in float vAlpha;
        out vec4 fragColor;
        uniform float uIsDark;
        void main() {
            vec2 c = gl_PointCoord - 0.5;
            float d = length(c);
            if (d > 0.5) discard;
            float a = vAlpha * (1.0 - d * 2.0);
            float nc = uIsDark > 0.5 ? 1.0 : 0.0;
            fragColor = vec4(nc, nc, nc, a * 0.3);
        }
    `;


    const cubeVS = `#version 300 es
        precision highp float;
        in vec2 aPosition;
        in vec3 aColor;
        in float aSize;
        in float aRotation;
        out vec3 vColor;
        out float vRotation;
        void main() {
            gl_Position = vec4(aPosition, 0.0, 1.0);
            gl_PointSize = aSize;
            vColor = aColor;
            vRotation = aRotation;
        }
    `;

    const cubeFS = `#version 300 es
        precision highp float;
        in vec3 vColor;
        in float vRotation;
        out vec4 fragColor;
        uniform float uHovered;
        void main() {
            vec2 p = gl_PointCoord - 0.5;
            vec2 ap = abs(p);
            float hw = 0.45, hh = 0.30;
            float dist = max(ap.x / hw, ap.y / hh);
            float outerGlow = smoothstep(1.0, 0.5, dist) * 0.12;
            if (ap.x > hw || ap.y > hh) {
                if (outerGlow < 0.01) discard;
                fragColor = vec4(vColor, outerGlow);
                return;
            }
            float edgeW = 0.016;
            bool onEdgeX = ap.x > hw - edgeW;
            bool onEdgeY = ap.y > hh - edgeW;
            float bracketLen = 0.13;
            float bracket = 0.0;
            if (onEdgeY && ap.x > hw - bracketLen) bracket = 1.0;
            if (onEdgeX && ap.y > hh - bracketLen) bracket = 1.0;
            float centerDot = smoothstep(0.022, 0.012, length(p));
            float scanY = sin(vRotation * 2.0) * hh * 0.7;
            float scanLine = smoothstep(0.01, 0.0, abs(p.y - scanY)) * 0.35;
            scanLine *= step(ap.x, hw - edgeW * 2.0);
            float fill = 0.08;
            float alpha = bracket * 0.9 + centerDot * 0.7 + scanLine + fill + outerGlow;
            if (uHovered > 0.5) {
                fill = 0.22;
                bracket = bracket > 0.0 ? 1.0 : 0.0;
                alpha = bracket * 1.0 + centerDot * 1.0 + scanLine * 2.0 + fill + outerGlow * 2.0;
                vec3 glow = mix(vColor, vec3(1.0), 0.3);
                fragColor = vec4(glow, min(alpha, 1.0));
            } else {
                fragColor = vec4(vColor, min(alpha, 1.0));
            }
        }
    `;


    const lineVS = `#version 300 es
        precision highp float;
        in vec2 aPosition;
        uniform float uAlpha;
        out float vAlpha;
        void main() {
            gl_Position = vec4(aPosition, 0.0, 1.0);
            vAlpha = uAlpha;
        }
    `;

    const lineFS = `#version 300 es
        precision highp float;
        in float vAlpha;
        out vec4 fragColor;
        uniform float uIsDark;
        void main() {
            float c = uIsDark > 0.5 ? 1.0 : 0.0;
            fragColor = vec4(c, c, c, vAlpha);
        }
    `;

    function compileShader(type, src) {
        const s = gl.createShader(type);
        gl.shaderSource(s, src);
        gl.compileShader(s);
        if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
            console.error(gl.getShaderInfoLog(s));
            return null;
        }
        return s;
    }

    function createProgram(vs, fs) {
        const p = gl.createProgram();
        gl.attachShader(p, compileShader(gl.VERTEX_SHADER, vs));
        gl.attachShader(p, compileShader(gl.FRAGMENT_SHADER, fs));
        gl.linkProgram(p);
        return p;
    }

    function noise(x, y) {
        return (Math.sin(x * 12.9898 + y * 78.233) * 43758.5453) % 1;
    }

    function simplex(x, y, t) {
        return Math.sin(x * 3.0 + t) * Math.cos(y * 2.5 + t * 0.7) * 0.5 +
               Math.sin(x * 7.0 - t * 1.3) * Math.cos(y * 5.0 + t) * 0.3 +
               Math.sin(x * 13.0 + t * 0.5) * Math.cos(y * 11.0 - t * 0.8) * 0.2;
    }

    function createMapCanvas() {
        mapCanvas = document.createElement('canvas');
        mapCanvas.width = 720;
        mapCanvas.height = 360;
        mapCtx = mapCanvas.getContext('2d', { willReadFrequently: true });

        mapCtx.fillStyle = '#ffffff';
        mapCtx.fillRect(0, 0, 720, 360);

        if (typeof countries !== 'undefined') {
            mapCtx.fillStyle = '#000000';
            for (const [_, r] of Object.entries(countries)) {
                if (!r.lat || !r.lon || r.lat.length < 3) continue;
                mapCtx.beginPath();
                const toX = lon => (lon + 180) / 360 * 720;
                const toY = lat => (90 - lat) / 180 * 360;
                mapCtx.moveTo(toX(r.lon[0]), toY(r.lat[0]));
                for (let i = 1; i < r.lat.length; i++) {
                    mapCtx.lineTo(toX(r.lon[i]), toY(r.lat[i]));
                }
                mapCtx.closePath();
                mapCtx.fill();
            }
        }
    }

    function isLand(u, v) {
        const x = Math.floor(u * 719), y = Math.floor(v * 359);
        if (x < 0 || x >= 720 || y < 0 || y >= 360) return false;
        return mapCtx.getImageData(x, y, 1, 1).data[0] < 128;
    }

    function getHeight(u, v) {
        const n1 = noise(u * 20, v * 20) * 0.5;
        const n2 = noise(u * 40, v * 40) * 0.3;
        const n3 = noise(u * 80, v * 80) * 0.2;
        return n1 + n2 + n3;
    }

    function latLonToXYZ(lat, lon, r) {
        const phi = (90 - lat) * Math.PI / 180;
        const theta = (lon + 180) * Math.PI / 180;
        return {
            x: -r * Math.sin(phi) * Math.cos(theta),
            y: r * Math.cos(phi),
            z: r * Math.sin(phi) * Math.sin(theta)
        };
    }

    function project(x, y, z, rx, ry, zm) {


        const cy = Math.cos(ry), sy = Math.sin(ry);
        let x1 = x * cy - z * sy;
        let z1 = x * sy + z * cy;


        const cx = Math.cos(rx), sx = Math.sin(rx);
        let y1 = y * cx - z1 * sx;
        let z2 = y * sx + z1 * cx;


        const camDist = zm;
        const zOffset = z2 + camDist;
        const fov = 1.2;
        const scale = fov / Math.max(zOffset, 0.1);
        let px = x1 * scale;
        let py = y1 * scale;


        const w = canvas.width || 1;
        const h = canvas.height || 1;
        if (w > h) {
            px *= h / w;
        } else {
            py *= w / h;
        }

        return { x: px, y: py, z: z2, scale, visible: true };
    }

    function hexToRGB(hex) {
        if (!hex) return [0.5, 0.1, 0.1];
        hex = hex.replace('#', '');
        if (hex.length === 3) hex = hex[0]+hex[0]+hex[1]+hex[1]+hex[2]+hex[2];
        const c = parseInt(hex, 16);
        return [(c >> 16 & 255) / 255, (c >> 8 & 255) / 255, (c & 255) / 255];
    }

    function parseGeo(str) {
        if (!str) return null;
        const m = str.match(/([+-]?\d+\.?\d*)/g);
        if (m && m.length >= 2) return { lat: parseFloat(m[0]), lon: parseFloat(m[1]) };
        return null;
    }


    function generateLand() {
        landPoints = [];
        for (let row = 0; row < GRID_ROWS; row++) {
            for (let col = 0; col < GRID_COLS; col++) {
                const u = col / GRID_COLS;
                const v = row / GRID_ROWS;

                if (isLand(u, v)) {
                    const lat = 90 - v * 180;
                    const lon = u * 360 - 180;
                    const h = getHeight(u, v) * 0.05;
                    const pos = latLonToXYZ(lat, lon, GLOBE_RADIUS + h);
                    landPoints.push({ x: pos.x, y: pos.y, z: pos.z, h, u, v });
                }
            }
        }
        landData = new Float32Array(landPoints.length * 4);
    }


    function generateOcean() {
        oceanPoints = [];
        for (let row = 0; row < OCEAN_ROWS; row++) {
            for (let col = 0; col < OCEAN_COLS; col++) {
                const u = col / OCEAN_COLS;
                const v = row / OCEAN_ROWS;

                if (!isLand(u, v)) {
                    const lat = 90 - v * 180;
                    const lon = u * 360 - 180;
                    const pos = latLonToXYZ(lat, lon, GLOBE_RADIUS);
                    oceanPoints.push({ x: pos.x, y: pos.y, z: pos.z, u, v, phase: Math.random() * Math.PI * 2 });
                }
            }
        }
        oceanData = new Float32Array(oceanPoints.length * 4);
    }


    function generateNoise() {
        noiseParticles = [];
        for (let i = 0; i < NOISE_COUNT; i++) {
            noiseParticles.push({
                x: (Math.random() - 0.5) * 2,
                y: (Math.random() - 0.5) * 2,
                vx: (Math.random() - 0.5) * 0.003,
                vy: (Math.random() - 0.5) * 0.003,
                size: 1.5 + Math.random() * 2.5,
                life: Math.random(),
                maxLife: 0.5 + Math.random() * 0.5
            });
        }
        noiseData = new Float32Array(noiseParticles.length * 4);
    }


    function generateBelarusBorder() {
        belarusBorder = [];

        const belarusData = (typeof t !== 'undefined') ? t : (typeof belarus !== 'undefined' ? belarus : null);
        if (belarusData && belarusData.length > 0) {
            for (let i = 0; i < belarusData.length; i++) {
                const [lon, lat] = belarusData[i]; 
                const pos = latLonToXYZ(lat, lon, GLOBE_RADIUS + 0.01);
                belarusBorder.push(pos);
            }
        } else {
        }
    }


    function generateDots() {
        dotPositions = [];
        dotColors = [];
        dotData = [];


        const belarusPos = latLonToXYZ(BELARUS.lat, BELARUS.lon, GLOBE_RADIUS + 0.03);
        dotPositions.push({ x: belarusPos.x, y: belarusPos.y, z: belarusPos.z, isBelarus: true });
        dotColors.push(1, 1, 1);
        dotData.push({ url: null, idx: 0 });


        if (typeof releases !== 'undefined') {
            releases.forEach((r, i) => {
                const geo = parseGeo(r.geo);
                if (!geo) return;
                const pos = latLonToXYZ(geo.lat, geo.lon, GLOBE_RADIUS + 0.03);
                const col = hexToRGB(r.color);
                dotPositions.push({ x: pos.x, y: pos.y, z: pos.z, isBelarus: false });
                dotColors.push(...col);
                dotData.push({ url: r.url, idx: i + 1 });
            });
        }
    }

    function generateLines() {
        lineData = [];
        if (dotPositions.length < 2) return;

        const ARC_SEGMENTS = 12;
        for (let i = 1; i < dotPositions.length; i++) {
            const from = dotPositions[0];
            const to = dotPositions[i];

            const fromLen = Math.sqrt(from.x * from.x + from.y * from.y + from.z * from.z);
            const toLen = Math.sqrt(to.x * to.x + to.y * to.y + to.z * to.z);
            const fx = from.x / fromLen, fy = from.y / fromLen, fz = from.z / fromLen;
            const tx = to.x / toLen, ty = to.y / toLen, tz = to.z / toLen;

            const dot = Math.max(-1, Math.min(1, fx * tx + fy * ty + fz * tz));
            const angle = Math.acos(dot);
            const sinAngle = Math.sin(angle);
            if (sinAngle < 0.001) {

                lineData.push({ points: [from, to] });
                continue;
            }
            const arcPoints = [];
            const arcRadius = (fromLen + toLen) / 2 + 0.015; 
            for (let s = 0; s <= ARC_SEGMENTS; s++) {
                const t = s / ARC_SEGMENTS;
                const a = Math.sin((1 - t) * angle) / sinAngle;
                const b = Math.sin(t * angle) / sinAngle;
                const px = (a * fx + b * tx) * arcRadius;
                const py = (a * fy + b * ty) * arcRadius;
                const pz = (a * fz + b * tz) * arcRadius;
                arcPoints.push({ x: px, y: py, z: pz });
            }
            lineData.push({ points: arcPoints });
        }
    }

    function initGL() {
        landProgram = createProgram(landVS, landFS);
        oceanProgram = createProgram(oceanVS, oceanFS);
        noiseProgram = createProgram(noiseVS, noiseFS);
        cubeProgram = createProgram(cubeVS, cubeFS);
        lineProgram = createProgram(lineVS, lineFS);

        gl.enable(gl.BLEND);
        gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);


        landVAO = gl.createVertexArray();
        gl.bindVertexArray(landVAO);
        landBuffer = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, landBuffer);
        gl.bufferData(gl.ARRAY_BUFFER, landData, gl.DYNAMIC_DRAW);
        const lPos = gl.getAttribLocation(landProgram, 'aPosition');
        const lD = gl.getAttribLocation(landProgram, 'aDepth');
        gl.enableVertexAttribArray(lPos);
        gl.vertexAttribPointer(lPos, 3, gl.FLOAT, false, 16, 0);
        gl.enableVertexAttribArray(lD);
        gl.vertexAttribPointer(lD, 1, gl.FLOAT, false, 16, 12);


        oceanVAO = gl.createVertexArray();
        gl.bindVertexArray(oceanVAO);
        oceanBuffer = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, oceanBuffer);
        gl.bufferData(gl.ARRAY_BUFFER, oceanData, gl.DYNAMIC_DRAW);
        const oPos = gl.getAttribLocation(oceanProgram, 'aPosition');
        const oA = gl.getAttribLocation(oceanProgram, 'aAlpha');
        gl.enableVertexAttribArray(oPos);
        gl.vertexAttribPointer(oPos, 3, gl.FLOAT, false, 16, 0);
        gl.enableVertexAttribArray(oA);
        gl.vertexAttribPointer(oA, 1, gl.FLOAT, false, 16, 12);


        noiseVAO = gl.createVertexArray();
        gl.bindVertexArray(noiseVAO);
        noiseBuffer = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, noiseBuffer);
        gl.bufferData(gl.ARRAY_BUFFER, noiseData, gl.DYNAMIC_DRAW);
        const nPos = gl.getAttribLocation(noiseProgram, 'aPosition');
        const nSize = gl.getAttribLocation(noiseProgram, 'aSize');
        const nA = gl.getAttribLocation(noiseProgram, 'aAlpha');
        gl.enableVertexAttribArray(nPos);
        gl.vertexAttribPointer(nPos, 2, gl.FLOAT, false, 16, 0);
        gl.enableVertexAttribArray(nSize);
        gl.vertexAttribPointer(nSize, 1, gl.FLOAT, false, 16, 8);
        gl.enableVertexAttribArray(nA);
        gl.vertexAttribPointer(nA, 1, gl.FLOAT, false, 16, 12);


        if (dotData.length > 0) {
            cubeVAO = gl.createVertexArray();
            gl.bindVertexArray(cubeVAO);
            cubeBuffer = gl.createBuffer();
            gl.bindBuffer(gl.ARRAY_BUFFER, cubeBuffer);
            gl.bufferData(gl.ARRAY_BUFFER, dotData.length * 28, gl.DYNAMIC_DRAW);
            const cPos = gl.getAttribLocation(cubeProgram, 'aPosition');
            const cCol = gl.getAttribLocation(cubeProgram, 'aColor');
            const cSize = gl.getAttribLocation(cubeProgram, 'aSize');
            const cRot = gl.getAttribLocation(cubeProgram, 'aRotation');
            gl.enableVertexAttribArray(cPos);
            gl.vertexAttribPointer(cPos, 2, gl.FLOAT, false, 28, 0);
            gl.enableVertexAttribArray(cCol);
            gl.vertexAttribPointer(cCol, 3, gl.FLOAT, false, 28, 8);
            gl.enableVertexAttribArray(cSize);
            gl.vertexAttribPointer(cSize, 1, gl.FLOAT, false, 28, 20);
            gl.enableVertexAttribArray(cRot);
            gl.vertexAttribPointer(cRot, 1, gl.FLOAT, false, 28, 24);
        }


        if (lineData.length > 0) {

            const maxLineSegments = lineData.length * 12;
            lineVAO = gl.createVertexArray();
            gl.bindVertexArray(lineVAO);
            lineBuffer = gl.createBuffer();
            gl.bindBuffer(gl.ARRAY_BUFFER, lineBuffer);
            gl.bufferData(gl.ARRAY_BUFFER, maxLineSegments * 16, gl.DYNAMIC_DRAW);
            const liPos = gl.getAttribLocation(lineProgram, 'aPosition');
            gl.enableVertexAttribArray(liPos);
            gl.vertexAttribPointer(liPos, 2, gl.FLOAT, false, 8, 0);
        }


        if (belarusBorder.length > 0) {
            belarusVAO = gl.createVertexArray();
            gl.bindVertexArray(belarusVAO);
            belarusBuffer = gl.createBuffer();
            gl.bindBuffer(gl.ARRAY_BUFFER, belarusBuffer);

            gl.bufferData(gl.ARRAY_BUFFER, belarusBorder.length * 16, gl.DYNAMIC_DRAW);
            const bPos = gl.getAttribLocation(lineProgram, 'aPosition');
            gl.enableVertexAttribArray(bPos);
            gl.vertexAttribPointer(bPos, 2, gl.FLOAT, false, 8, 0);
        }

        gl.bindVertexArray(null);
    }

    function resize() {
        const dpr = Math.min(window.devicePixelRatio || 1, 2);
        const rect = canvas.getBoundingClientRect();
        const w = Math.max(1, rect.width);
        const h = Math.max(1, rect.height);
        if (canvas.width !== Math.round(w * dpr) || canvas.height !== Math.round(h * dpr)) {
            canvas.width = Math.round(w * dpr);
            canvas.height = Math.round(h * dpr);
            gl.viewport(0, 0, canvas.width, canvas.height);
        }
    }


    function setupInteraction() {
        canvas.addEventListener('mousedown', e => {
            isDragging = true;
            wasDrag = false;
            autoRotate = false;
            lastMouse = { x: e.clientX, y: e.clientY };
            canvas.style.cursor = 'grabbing';
        });

        window.addEventListener('mousemove', e => {
            const rect = canvas.getBoundingClientRect();
            const mx = ((e.clientX - rect.left) / rect.width) * 2 - 1;
            const my = -((e.clientY - rect.top) / rect.height) * 2 + 1;
            let newHovered = -1;
            for (let i = 0; i < dotPositions.length; i++) {
                const d = dotPositions[i];
                const p = project(d.x, d.y, d.z, rotation.x, rotation.y, zoom);
                const hitRadius = 0.05 * p.scale;
                if (p.visible && Math.hypot(p.x - mx, p.y - my) < Math.max(hitRadius, 0.04)) {
                    newHovered = i;
                    break;
                }
            }
            hoveredDot = newHovered;
            if (!isDragging) {
                canvas.style.cursor = hoveredDot >= 0 ? 'pointer' : 'grab';
            }
            if (!isDragging) return;
            const dx = e.clientX - lastMouse.x;
            const dy = e.clientY - lastMouse.y;
            if (Math.abs(dx) > 2 || Math.abs(dy) > 2) {
                wasDrag = true;
            }
            const zoomFactor = 0.75 + (targetZoom / ZOOM_MAX) * 0.25;
            const dragScale = 0.005 * zoomFactor;

            targetRotation.y += dx * dragScale;
            targetRotation.x = clampTilt(targetRotation.x - dy * dragScale);
            lastMouse = { x: e.clientX, y: e.clientY };
        });

        window.addEventListener('mouseup', e => {
            if (isDragging && !wasDrag) handleClick(e);
            isDragging = false;
            canvas.style.cursor = hoveredDot >= 0 ? 'pointer' : 'grab';
        });

        canvas.addEventListener('wheel', e => {
            e.preventDefault();
            const zoomSpeed = 0.0008 * targetZoom;
            targetZoom = Math.max(ZOOM_MIN, Math.min(ZOOM_MAX, targetZoom + e.deltaY * zoomSpeed));
        }, { passive: false });


        canvas.addEventListener('touchstart', e => {
            e.preventDefault();
            if (e.touches.length === 1) {
                isDragging = true;
                wasDrag = false;
                autoRotate = false;
                lastMouse = { x: e.touches[0].clientX, y: e.touches[0].clientY };
            } else if (e.touches.length === 2) {
                const dx = e.touches[0].clientX - e.touches[1].clientX;
                const dy = e.touches[0].clientY - e.touches[1].clientY;
                pinchDist = Math.sqrt(dx * dx + dy * dy);
            }
        }, { passive: false });

        canvas.addEventListener('touchmove', e => {
            e.preventDefault();
            if (e.touches.length === 1 && isDragging) {
                const dx = e.touches[0].clientX - lastMouse.x;
                const dy = e.touches[0].clientY - lastMouse.y;
                if (Math.abs(dx) > 1 || Math.abs(dy) > 1) {
                    wasDrag = true;
                }
                const zoomFactor = 0.75 + (targetZoom / ZOOM_MAX) * 0.25;
                const dragScale = 0.007 * zoomFactor;
                targetRotation.y += dx * dragScale;
                targetRotation.x = clampTilt(targetRotation.x - dy * dragScale);
                lastMouse = { x: e.touches[0].clientX, y: e.touches[0].clientY };
            } else if (e.touches.length === 2) {
                const dx = e.touches[0].clientX - e.touches[1].clientX;
                const dy = e.touches[0].clientY - e.touches[1].clientY;
                const dist = Math.sqrt(dx * dx + dy * dy);
                const pinchSpeed = 0.001 * targetZoom;
                targetZoom = Math.max(ZOOM_MIN, Math.min(ZOOM_MAX, targetZoom - (dist - pinchDist) * pinchSpeed));
                pinchDist = dist;
            }
        }, { passive: false });

        canvas.addEventListener('touchend', e => {
            if (isDragging && !wasDrag && e.changedTouches.length === 1) {
                handleClick({ clientX: e.changedTouches[0].clientX, clientY: e.changedTouches[0].clientY });
            }
            isDragging = false;
        }, { passive: true });

        canvas.style.cursor = 'grab';
    }

    function handleClick(e) {
        const rect = canvas.getBoundingClientRect();
        const mx = ((e.clientX - rect.left) / rect.width) * 2 - 1;
        const my = -((e.clientY - rect.top) / rect.height) * 2 + 1;

        for (let i = 0; i < dotPositions.length; i++) {
            const d = dotPositions[i];
            const p = project(d.x, d.y, d.z, rotation.x, rotation.y, zoom);
            const hitRadius = 0.04 * p.scale; 
            if (p.visible && Math.hypot(p.x - mx, p.y - my) < Math.max(hitRadius, 0.03)) {
                if (dotData[i].url) {
                    window.location.href = dotData[i].url;
                }
                break;
            }
        }
    }

    function render() {
        if (!isVisible) { requestAnimationFrame(render); return; }

        time += 0.016;
        if (autoRotate) targetRotation.y += 0.0005;

        const lerpSpeed = isDragging ? 0.25 : 0.08;
        rotation.x += (targetRotation.x - rotation.x) * lerpSpeed;
        rotation.y += (targetRotation.y - rotation.y) * lerpSpeed;
        zoom += (targetZoom - zoom) * 0.1;


        let landCount = 0;
        for (let i = 0; i < landPoints.length; i++) {
            const p = landPoints[i];
            const proj = project(p.x, p.y, p.z, rotation.x, rotation.y, zoom);
            if (proj.visible) {
                landData[landCount * 4] = proj.x;
                landData[landCount * 4 + 1] = proj.y;
                landData[landCount * 4 + 2] = proj.z;
                landData[landCount * 4 + 3] = (proj.z + GLOBE_RADIUS) / (GLOBE_RADIUS * 2);
                landCount++;
            }
        }


        let oceanCount = 0;
        for (let i = 0; i < oceanPoints.length; i++) {
            const p = oceanPoints[i];
            const wave = simplex(p.u * 10, p.v * 10, time * 0.5);
            const alpha = 0.2 + wave * 0.2 + Math.sin(time * 1.5 + p.phase) * 0.15;
            const proj = project(p.x, p.y, p.z, rotation.x, rotation.y, zoom);
            if (proj.visible && alpha > 0.1) {
                oceanData[oceanCount * 4] = proj.x;
                oceanData[oceanCount * 4 + 1] = proj.y;
                oceanData[oceanCount * 4 + 2] = proj.z;
                oceanData[oceanCount * 4 + 3] = Math.max(0, Math.min(1, alpha));
                oceanCount++;
            }
        }


        for (let i = 0; i < noiseParticles.length; i++) {
            const n = noiseParticles[i];
            n.x += n.vx + Math.sin(time + i) * 0.001;
            n.y += n.vy + Math.cos(time * 0.7 + i) * 0.001;
            n.life += 0.008;
            if (n.life > n.maxLife || Math.abs(n.x) > 1.2 || Math.abs(n.y) > 1.2) {
                n.x = (Math.random() - 0.5) * 2;
                n.y = (Math.random() - 0.5) * 2;
                n.life = 0;
            }
            const alpha = n.life < 0.2 ? n.life * 5 : n.life > 0.8 ? (1 - n.life) * 5 : 1;
            noiseData[i * 4] = n.x;
            noiseData[i * 4 + 1] = n.y;
            noiseData[i * 4 + 2] = n.size;
            noiseData[i * 4 + 3] = alpha;
        }


        const cubeBuf = new Float32Array(dotPositions.length * 7);
        const projectedDots = [];
        for (let i = 0; i < dotPositions.length; i++) {
            const d = dotPositions[i];
            const proj = project(d.x, d.y, d.z, rotation.x, rotation.y, zoom);
            projectedDots.push(proj);
            const cubeRot = time * 0.15 + i * 0.5;
            const size = proj.visible ? CUBE_SIZE * proj.scale : 0;
            cubeBuf[i * 7] = proj.x;
            cubeBuf[i * 7 + 1] = proj.y;
            cubeBuf[i * 7 + 2] = dotColors[i * 3];
            cubeBuf[i * 7 + 3] = dotColors[i * 3 + 1];
            cubeBuf[i * 7 + 4] = dotColors[i * 3 + 2];
            cubeBuf[i * 7 + 5] = size;
            cubeBuf[i * 7 + 6] = cubeRot;
        }


        const maxSegments = lineData.length * 12;
        const lineBuf = new Float32Array(maxSegments * 4);
        let lineSegCount = 0;
        for (let i = 0; i < lineData.length; i++) {
            const pts = lineData[i].points;
            for (let s = 0; s < pts.length - 1; s++) {
                const p1 = project(pts[s].x, pts[s].y, pts[s].z, rotation.x, rotation.y, zoom);
                const p2 = project(pts[s + 1].x, pts[s + 1].y, pts[s + 1].z, rotation.x, rotation.y, zoom);
                if (p1.visible && p2.visible) {
                    lineBuf[lineSegCount * 4] = p1.x;
                    lineBuf[lineSegCount * 4 + 1] = p1.y;
                    lineBuf[lineSegCount * 4 + 2] = p2.x;
                    lineBuf[lineSegCount * 4 + 3] = p2.y;
                    lineSegCount++;
                }
            }
        }


        const belarusBuf = new Float32Array(belarusBorder.length * 2 * 2);
        let belarusLineCount = 0;
        for (let i = 0; i < belarusBorder.length; i++) {
            const p1 = belarusBorder[i];
            const p2 = belarusBorder[(i + 1) % belarusBorder.length];
            const proj1 = project(p1.x, p1.y, p1.z, rotation.x, rotation.y, zoom);
            const proj2 = project(p2.x, p2.y, p2.z, rotation.x, rotation.y, zoom);
            if (proj1.visible && proj2.visible) {
                belarusBuf[belarusLineCount * 4] = proj1.x;
                belarusBuf[belarusLineCount * 4 + 1] = proj1.y;
                belarusBuf[belarusLineCount * 4 + 2] = proj2.x;
                belarusBuf[belarusLineCount * 4 + 3] = proj2.y;
                belarusLineCount++;
            }
        }


        const isDark = document.documentElement.getAttribute('data-wiehr-theme') === 'dark';
        if (isDark) {

            gl.clearColor(0.0824, 0.0863, 0.0902, 1.0);
        } else {
            gl.clearColor(0.957, 0.957, 0.957, 1.0);
        }
        gl.clear(gl.COLOR_BUFFER_BIT);

        var darkVal = isDark ? 1.0 : 0.0;


        gl.useProgram(oceanProgram);
        gl.uniform1f(gl.getUniformLocation(oceanProgram, 'uPointSize'), POINT_SIZE);
        gl.uniform1f(gl.getUniformLocation(oceanProgram, 'uIsDark'), darkVal);
        gl.bindVertexArray(oceanVAO);
        gl.bindBuffer(gl.ARRAY_BUFFER, oceanBuffer);
        gl.bufferSubData(gl.ARRAY_BUFFER, 0, oceanData);
        gl.drawArrays(gl.POINTS, 0, oceanCount);


        gl.useProgram(landProgram);
        gl.uniform1f(gl.getUniformLocation(landProgram, 'uPointSize'), POINT_SIZE);
        gl.uniform1f(gl.getUniformLocation(landProgram, 'uIsDark'), darkVal);
        gl.bindVertexArray(landVAO);
        gl.bindBuffer(gl.ARRAY_BUFFER, landBuffer);
        gl.bufferSubData(gl.ARRAY_BUFFER, 0, landData);
        gl.drawArrays(gl.POINTS, 0, landCount);


        if (lineVAO && lineSegCount > 0) {
            gl.useProgram(lineProgram);
            gl.uniform1f(gl.getUniformLocation(lineProgram, 'uAlpha'), 0.2);
            gl.uniform1f(gl.getUniformLocation(lineProgram, 'uIsDark'), darkVal);
            gl.bindVertexArray(lineVAO);
            gl.bindBuffer(gl.ARRAY_BUFFER, lineBuffer);
            gl.bufferSubData(gl.ARRAY_BUFFER, 0, lineBuf.subarray(0, lineSegCount * 4));
            gl.drawArrays(gl.LINES, 0, lineSegCount * 2);
        }


        if (belarusVAO && belarusLineCount > 0) {
            gl.useProgram(lineProgram);
            gl.uniform1f(gl.getUniformLocation(lineProgram, 'uIsDark'), darkVal);
            gl.bindVertexArray(belarusVAO);
            gl.bindBuffer(gl.ARRAY_BUFFER, belarusBuffer);
            gl.bufferSubData(gl.ARRAY_BUFFER, 0, belarusBuf);

            const glowPasses = [0.15, 0.25, 0.4, 0.9];
            for (let g = 0; g < glowPasses.length; g++) {
                gl.uniform1f(gl.getUniformLocation(lineProgram, 'uAlpha'), glowPasses[g]);
                gl.drawArrays(gl.LINES, 0, belarusLineCount * 2);
            }
        }


        if (cubeVAO && dotData.length > 1) {
            gl.useProgram(cubeProgram);
            for (let i = 1; i < dotPositions.length; i++) {
                const singleBuf = new Float32Array(7);
                for (let j = 0; j < 7; j++) singleBuf[j] = cubeBuf[i * 7 + j];
                gl.uniform1f(gl.getUniformLocation(cubeProgram, 'uHovered'), hoveredDot === i ? 1.0 : 0.0);
                gl.bindVertexArray(cubeVAO);
                gl.bindBuffer(gl.ARRAY_BUFFER, cubeBuffer);
                gl.bufferSubData(gl.ARRAY_BUFFER, 0, singleBuf);
                gl.drawArrays(gl.POINTS, 0, 1);
            }
        }


        gl.useProgram(noiseProgram);
        gl.uniform1f(gl.getUniformLocation(noiseProgram, 'uIsDark'), darkVal);
        gl.bindVertexArray(noiseVAO);
        gl.bindBuffer(gl.ARRAY_BUFFER, noiseBuffer);
        gl.bufferSubData(gl.ARRAY_BUFFER, 0, noiseData);
        gl.drawArrays(gl.POINTS, 0, noiseParticles.length);

        requestAnimationFrame(render);
    }

    function init() {
        canvas = document.getElementById('spinmedizzy');
        if (!canvas) return false;

        gl = canvas.getContext('webgl2', {
            alpha: false,
            antialias: true,
            depth: false,
            powerPreference: 'high-performance'
        });

        if (!gl) return false;

        resize();
        window.addEventListener('resize', resize);
        return true;
    }

    function start() {
        if (typeof countries !== 'undefined') {
            createMapCanvas();
            generateLand();
            generateOcean();
            generateNoise();
            generateBelarusBorder();
            generateDots();
            generateLines();
            initGL();
            setupInteraction();
            resize();

            window.addEventListener('resize', resize);

            render();
            window.globeInitialized = true;
        } else {
            setTimeout(start, 100);
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => { if (init()) start(); });
    } else {
        if (init()) start();
    }

    document.addEventListener('visibilitychange', () => { isVisible = !document.hidden; });
})();
