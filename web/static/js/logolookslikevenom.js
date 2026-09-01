const canvas = document.getElementById("pleasesavemefromthis");
if (!canvas) {
  console.error('Canvas element not found');
  throw new Error('Canvas element #gl not found');
}

const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) || window.innerWidth <= 640;

const gl = canvas.getContext("webgl2", {
  alpha: true,
  antialias: false,
  depth: false,
  stencil: true,
  powerPreference: "high-performance",
  failIfMajorPerformanceCaveat: false,
  desynchronized: true
});

if (!gl) {
  console.error('WebGL2 not supported, hiding canvas');
  canvas.style.display = 'none';
  throw new Error('WebGL2 not supported');
}

function resizeCanvas() {

  const content = document.getElementById('content') || document.getElementById('whatareyouinterestedin');


  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  canvas.style.width = '100%';
  canvas.style.height = '100%';
  canvas.style.position = 'fixed';
  canvas.style.top = '0';
  canvas.style.left = '0';
  canvas.style.zIndex = '1';


  if (gl) {
    gl.viewport(0, 0, canvas.width, canvas.height);
  }
}

resizeCanvas();


let isLogoSectionVisible = true;


const initialSection = document.querySelector('.anchor-section[style*="display: block"]');
if (initialSection && initialSection.id !== 'section-pleasesavemefromthis') {
  isLogoSectionVisible = false;
  canvas.style.display = 'none';
}
let lastCanvasWidth = 0;
let lastCanvasHeight = 0;


function forceCanvasReset() {
  const targetWidth = window.innerWidth;
  const targetHeight = window.innerHeight;


  if (lastCanvasWidth === targetWidth && lastCanvasHeight === targetHeight) {
    return;
  }

  lastCanvasWidth = targetWidth;
  lastCanvasHeight = targetHeight;


  canvas.width = targetWidth;
  canvas.height = targetHeight;
  canvas.style.width = targetWidth + 'px';
  canvas.style.height = targetHeight + 'px';


  if (gl) {
    gl.viewport(0, 0, targetWidth, targetHeight);
  }
}


window.addEventListener('sectionchange', (e) => {
  if (e.detail) {
    const goingToLogo = e.detail.to === 0;
    const leavingLogo = e.detail.from === 0 && e.detail.to !== 0;

    if (leavingLogo) {

      isLogoSectionVisible = false;
      if (window.pauseWebGL) {
        window.pauseWebGL();
      }

      canvas.style.display = 'none';
    }

    if (goingToLogo) {

      isLogoSectionVisible = true;
      canvas.style.display = 'block';


      lastCanvasWidth = 0;
      lastCanvasHeight = 0;


      forceCanvasReset();
      setTimeout(forceCanvasReset, 50);
      setTimeout(() => {
        forceCanvasReset();

        if (window.resumeWebGL) {
          window.resumeWebGL();
        }
      }, 150);
    }
  }
});


document.addEventListener('visibilitychange', () => {
  if (!document.hidden && isLogoSectionVisible) {
    lastCanvasWidth = 0;
    lastCanvasHeight = 0;
    setTimeout(forceCanvasReset, 100);
  }
});


let resizeTimeout = null;
window.addEventListener('resize', () => {
  if (!isLogoSectionVisible) return;
  clearTimeout(resizeTimeout);
  resizeTimeout = setTimeout(() => {
    lastCanvasWidth = 0;
    lastCanvasHeight = 0;
    forceCanvasReset();
  }, 100);
});


const svg = `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 3000 3000"><path d="M1063.3,2651.4l42.9,3.5v89.3h-90.6v85.2l-46.2,3.5v81.7H876.5V2834H831v80H738.8v-80.7H691.5v80.4l-45.3,5.9V3000H368.1V2832.2H276.9V2661.1H137.2v-84.9h-45c-1.2,26.4-2.4,53-3.6,81.6H45.9v-81L0,2572.4v-88.2l43-4.8v-81.5h92.4V2225.8H412V2055.6h45.6v81.1h48.5v-82.1h91.1v-85.8h94v-84.5l44.3-3.9V1718.9H369.8V1539.6H550.9V1371.1l45.4-4.9v-75l-43.5-3.5v-81.2H460.1v81.1h-91v-83.1H277.6v-90.8l41.2-4.5v-83.1H460.3V942.5l45.5-4.7V856.9h91.1v80.3h94.3V855h91.2V771.3l45.3-4.7V691.9l-44-3.9V607l-44.1-4.5V520.1H600V433.3H507.4V349.1H370V170.9l41.4-3.6c1.1-26.4,2.3-53,3.6-82.5H597.3V0h47.1V81.4h92.7V253.8H875.5v85.3h91.1v84l47.3,5.1v81.5h45.8V428.4h230.8v82.3H1430v85.6h91.6v84.5h92.3V599.9h47V683h138V859.8H1711c-1.4,29.5-2.6,56.1-4,84.7l-43.1,4.5v162.4h90v340.3H1845v-80.8h47v82.8h138.6v85.1h140.3v83.6l45.4,4.9v80.4l44.9,5.6v173l-43.7,5.4v80.6l-44.2,4.5v246.8h134.6v-82.9h45.7v82h92.8V2056.2h46.7v81.4H2539v-82.4l48.5-3.4v-82.3h229.3v82.6h93v85.8H3000v178.8h-88.3v84.7h-92.9V2488H2634.6v85.4H2218v170.5h-92.8v86.7h-93.1v169.2H1846.8v-79.5l-45.5-5.9V2746.7H1615.8v-85.5H1153.7V2577h-90.4Zm690.2-856.5v-82.4l45-3.5v-74.3H1617.3v73.9l44.8,5v81.3Zm-2.2,685.4V2319.5h-40.6v160.8ZM1848,2308h88.8v-74.5H1848ZM971,2575.9v77.3l40.5-1.8v-75.5Z"/></svg>
`

const svgComplexity = svg.length;
const maskSize = isMobile ? 60 : 120;
const mask = document.createElement("canvas");
mask.width = maskSize;
mask.height = maskSize;

const mctx = mask.getContext("2d", { willReadFrequently: true });
mctx.imageSmoothingEnabled = false;


const img = new Image();
const svgBlob = new Blob([svg], { type: "image/svg+xml;charset=utf-8" });
const url = URL.createObjectURL(svgBlob);
img.src = url;

img.onload = () => {
  mctx.clearRect(0, 0, mask.width, mask.height);
  mctx.drawImage(img, 0, 0, mask.width, mask.height);
  URL.revokeObjectURL(url);

  try {
    buildTargets();
    initGL();
    loadNetworkData();
    render(0);
  } catch (error) {
    console.error('Error initializing WebGL:', error);
    canvas.style.display = 'none';
  }
};

img.onerror = () => {
  console.error('Failed to load SVG image');
  canvas.style.display = 'none';
  URL.revokeObjectURL(url);
};


let particles = [];
let COUNT = 0;
let positions, posBuf;
let venomValues, venomBuf;


let networkParticles = [];
let networkCount = 0;
let logoParticleCount = 0;
window._networkProjected = [];
window._networkTime = 0;
window._networkMouseScreen = { x: 0, y: 0 };

class NetworkParticle {
  constructor(destX, destY, phase) {
    this.x = (Math.random() * 2 - 1) * 1.5;
    this.y = (Math.random() * 2 - 1) * 1.5;
    this.destX = destX;
    this.destY = destY;
    this.phase = phase;
    this.vx = 0;
    this.vy = 0;
  }

  update(time, mouseScreenX, mouseScreenY) {
    const breathe = Math.sin(time * 0.2 + this.phase) * 0.03 + 1;
    const driftX = Math.sin(time * 0.35 + this.phase) * 0.008
      + Math.sin(time * 0.12 + this.phase * 2.7) * 0.005;
    const driftY = Math.cos(time * 0.28 + this.phase * 1.3) * 0.006
      + Math.cos(time * 0.09 + this.phase * 3.1) * 0.004;
    const depthFactor = 0.7 + (this.phase / (Math.PI * 2)) * 0.6;
    const globalDriftX = mouseScreenX * 0.06 * depthFactor;
    const globalDriftY = mouseScreenY * 0.04 * depthFactor;

    const targetX = this.destX * breathe + driftX + globalDriftX;
    const targetY = this.destY * breathe + driftY + globalDriftY;

    this.vx += (targetX - this.x) * 0.04;
    this.vy += (targetY - this.y) * 0.04;
    this.vx *= 0.88;
    this.vy *= 0.88;
    this.x += this.vx;
    this.y += this.vy;
  }
}

function countryToAngle(code, index, total) {
  let hash = 0;
  for (let i = 0; i < code.length; i++) {
    hash = ((hash << 5) - hash) + code.charCodeAt(i);
    hash |= 0;
  }
  const base = (index / total) * Math.PI * 2;
  const offset = (Math.abs(hash) % 100) / 100 * (Math.PI * 2 / total) * 0.4;
  return base + offset - Math.PI / 2;
}

function buildNetworkParticles(locations) {
  networkParticles = [];
  if (!locations || locations.length === 0) return;

  const baseRadius = 0.45;
  const total = locations.length;

  for (let i = 0; i < locations.length; i++) {
    const loc = locations[i];
    const angle = countryToAngle(loc.code || loc.country, i, total);
    const destX = Math.cos(angle) * baseRadius;
    const destY = Math.sin(angle) * baseRadius;
    const phase = Math.random() * Math.PI * 2;

    const np = new NetworkParticle(destX, destY, phase);
    np._isChild = false;
    np._parentIdx = -1;
    np._country = loc.country;
    np._code = loc.code || '';
    networkParticles.push(np);
    const parentIdx = networkParticles.length - 1;

    if (loc.count > 1) {
      for (let c = 0; c < loc.count - 1; c++) {
        const childOffset = (c % 2 === 0 ? 1 : -1) * (Math.floor(c / 2) + 1);
        const childAngle = angle + childOffset * 0.06;
        const childRadius = baseRadius + 0.06 + c * 0.04;
        const cx = Math.cos(childAngle) * childRadius;
        const cy = Math.sin(childAngle) * childRadius;
        const cp = new NetworkParticle(cx, cy, Math.random() * Math.PI * 2);
        cp._isChild = true;
        cp._parentIdx = parentIdx;
        cp._country = loc.country;
        cp._code = loc.code || '';
        networkParticles.push(cp);
      }
    }
  }

  networkCount = networkParticles.length;
  rebuildPositionsArray();
}

function rebuildPositionsArray() {
  const totalCount = logoParticleCount + networkCount;
  COUNT = totalCount;
  const newPositions = new Float32Array(totalCount * 2);
  if (positions) {
    newPositions.set(positions.subarray(0, Math.min(positions.length, logoParticleCount * 2)));
  }
  positions = newPositions;

  const newVenom = new Float32Array(totalCount);
  if (venomValues) {
    newVenom.set(venomValues.subarray(0, Math.min(venomValues.length, logoParticleCount)));
  }
  venomValues = newVenom;

  if (posBuf && gl) {
    gl.bindBuffer(gl.ARRAY_BUFFER, posBuf);
    gl.bufferData(gl.ARRAY_BUFFER, positions, gl.DYNAMIC_DRAW);
  }
  if (venomBuf && gl) {
    gl.bindBuffer(gl.ARRAY_BUFFER, venomBuf);
    gl.bufferData(gl.ARRAY_BUFFER, venomValues, gl.DYNAMIC_DRAW);
  }
}

function loadNetworkData() {
  fetch('/api/network/locations').then(r => r.json()).then(data => {
    buildNetworkParticles(data);
  }).catch(() => {});
}
window._reloadNetwork = function() {
  fetch('/api/network/locations?t=' + Date.now()).then(r => r.json()).then(data => {
    buildNetworkParticles(data);
  }).catch(() => {});
};

class Particle {
  constructor(destX, destY) {
    this.x = (Math.random() * 2 - 1) * 1.8;
    this.y = (Math.random() * 2 - 1) * 1.8;
    this.z = (Math.random() - 0.5) * 0.2;
    this.destX = destX;
    this.destY = destY;
    this.destZ = 0;
    this.speed = Math.random() * 0.02 + 0.045;
    this.friction = 0.82;
    this.vx = 0;
    this.vy = 0;
    this.vz = 0;
    this.inVacuum = false;
    this.venomStrength = 0;
    this.neighbors = [];
  }

  update(mouseX, mouseY, isVacuum, mouseVelX, mouseVelY, time, chaoticForces, cursorSize, vacuumRadius) {
    const dx = this.destX - this.x;
    const dy = this.destY - this.y;
    const dz = this.destZ - this.z;
    const distFromDest = Math.sqrt(dx * dx + dy * dy);

    const returnForce = this.inVacuum ? 0.004 : this.speed;
    this.vx += dx * returnForce;
    this.vy += dy * returnForce;
    this.vz += dz * returnForce * 0.8;

    const inLogoShape = distFromDest < 0.05;
    if (inLogoShape) {
      for (let i = 0; i < chaoticForces.length; i++) {
        this.vx += chaoticForces[i].fx;
        this.vy += chaoticForces[i].fy;
        this.vz += chaoticForces[i].fz;
      }

      for (let i = 0; i < this.neighbors.length; i++) {
        const n = this.neighbors[i];
        const ndx = n.x - this.x;
        const ndy = n.y - this.y;
        const ndist = Math.sqrt(ndx * ndx + ndy * ndy);
        if (ndist > 0.001 && ndist < 0.04) {
          const commForce = 0.0002 * (1.0 - ndist / 0.04);
          const repel = ndist < 0.015 ? -1 : 1;
          const normFactor = commForce * repel / ndist;
          this.vx += ndx * normFactor;
          this.vy += ndy * normFactor;
        }
      }
    }

    if (mouseX !== null && mouseY !== null) {
      const mdx = mouseX - this.x;
      const mdy = mouseY - this.y;
      const absX = Math.abs(mdx);
      const absY = Math.abs(mdy);
      const squareDist = Math.max(absX, absY);

      if (isVacuum) {
        if (absX < vacuumRadius && absY < vacuumRadius) {
          const edgeDist = vacuumRadius - squareDist;
          const pullStrength = 0.002 * (edgeDist / vacuumRadius);

          const chaoticX = Math.sin(time * 2 + this.x * 15) * 0.001;
          const chaoticY = Math.cos(time * 2.3 + this.y * 15) * 0.001;

          this.vx += (Math.sign(mdx) + chaoticX) * pullStrength;
          this.vy += (Math.sign(mdy) + chaoticY) * pullStrength;
          this.vz += Math.sin(time * 3 + squareDist * 20) * pullStrength * 0.3;
          this.inVacuum = true;
          this.venomStrength = Math.min(1.0, this.venomStrength + 0.05);
        } else {
          this.inVacuum = false;
        }
      } else {
        this.inVacuum = false;

        if (absX < cursorSize && absY < cursorSize) {
          const edgeDistX = cursorSize - absX;
          const edgeDistY = cursorSize - absY;
          const minEdgeDist = Math.min(edgeDistX, edgeDistY);
          const pushStrength = Math.pow(minEdgeDist / cursorSize, 2.5) * 0.08;

          this.vx -= Math.sign(mdx) * pushStrength;
          this.vy -= Math.sign(mdy) * pushStrength;
          this.vz -= (Math.random() - 0.5) * pushStrength * 0.5;

          this.venomStrength = Math.min(1.0, this.venomStrength + 0.08);
        }

        const mouseSpeed = Math.sqrt(mouseVelX * mouseVelX + mouseVelY * mouseVelY);
        if (mouseSpeed > 0.03) {
          const sliceSize = cursorSize * 2.5;
          if (absX < sliceSize && absY < sliceSize) {
            const sliceForce = mouseSpeed * 1.8;
            const perpX = mouseVelY * sliceForce;
            const perpY = -mouseVelX * sliceForce;

            const side = Math.sign(mdx * mouseVelY - mdy * mouseVelX);
            this.vx += perpX * side * 0.6;
            this.vy += perpY * side * 0.6;

            this.venomStrength = Math.min(1.0, this.venomStrength + 0.15);
          }
        }
      }
    } else {
      this.inVacuum = false;
    }

    this.venomStrength *= 0.92;

    this.vx *= this.friction;
    this.vy *= this.friction;
    this.vz *= 0.92;

    const maxSpeed = 0.22;
    const speed = Math.sqrt(this.vx * this.vx + this.vy * this.vy + this.vz * this.vz);
    if (speed > maxSpeed) {
      this.vx = (this.vx / speed) * maxSpeed;
      this.vy = (this.vy / speed) * maxSpeed;
      this.vz = (this.vz / speed) * maxSpeed;
    }

    this.x += this.vx;
    this.y += this.vy;
    this.z += this.vz;
  }

  /* The hot path: no trig, no object.

     getProjected3D below recomputes cos/sin of the SAME two rotation angles
     for every particle - four trig calls per particle per frame, when the
     angles change once per frame - and returns a fresh {x, y, scale} that is
     read twice and thrown away. At a thousand particles and 60fps that is a
     quarter of a million redundant trig calls and sixty thousand short-lived
     objects a second, which is GC pressure disguised as maths.

     This takes the trig already done for the frame and writes the result
     straight into the position buffer. */
  projectInto(cosY, sinY, cosX, sinX, canvasAspect, out, idx) {
    const x1 = this.x * cosY - this.z * sinY;
    const z1 = this.x * sinY + this.z * cosY;

    const y2 = this.y * cosX - z1 * sinX;
    const z2 = this.y * sinX + z1 * cosX;

    const focalLength = 2.5;
    const perspective = focalLength / (focalLength + z2);
    let projX = x1 * perspective;
    let projY = y2 * perspective;

    if (canvasAspect > 1.0) {
      projY *= canvasAspect;
    } else {
      projX /= canvasAspect;
    }

    const spacingFactor = 0.98;
    out[idx] = projX * spacingFactor;
    out[idx + 1] = projY * spacingFactor;
  }

  getProjected3D(rotX, rotY, canvasAspect) {
    const cosY = Math.cos(rotY);
    const sinY = Math.sin(rotY);
    const cosX = Math.cos(rotX);
    const sinX = Math.sin(rotX);

    let x1 = this.x * cosY - this.z * sinY;
    let z1 = this.x * sinY + this.z * cosY;

    let y2 = this.y * cosX - z1 * sinX;
    let z2 = this.y * sinX + z1 * cosX;

    const focalLength = 2.5;
    const perspective = focalLength / (focalLength + z2);
    let projX = x1 * perspective;
    let projY = y2 * perspective;

    if (canvasAspect > 1.0) {
      projY *= canvasAspect;
    } else {
      projX /= canvasAspect;
    }

    const spacingFactor = 0.98;

    return {
      x: projX * spacingFactor,
      y: projY * spacingFactor,
      scale: perspective
    };
  }
}

function getPerformanceTier() {

  const cores = navigator.hardwareConcurrency || 2;
  const mem = navigator.deviceMemory || 2;


  let gpuTier = 2;
  const debugExt = gl.getExtension('WEBGL_debug_renderer_info');
  if (debugExt) {
    const renderer = gl.getParameter(debugExt.UNMASKED_RENDERER_WEBGL).toLowerCase();
    if (renderer.includes('nvidia') || renderer.includes('radeon rx') || renderer.includes('apple m')) {
      gpuTier = 1;
    } else if (renderer.includes('intel iris') || renderer.includes('radeon pro') || renderer.includes('apple gpu')) {
      gpuTier = 1;
    } else if (renderer.includes('intel hd') || renderer.includes('intel uhd') || renderer.includes('adreno 6')) {
      gpuTier = 2;
    } else if (renderer.includes('mali') || renderer.includes('adreno 5') || renderer.includes('powervr')) {
      gpuTier = 3;
    }
  }

  if (isMobile) {
    // Safari implements no deviceMemory at all, so `mem` falls back to 2 and
    // both tests below used to fail — every iPhone landed in tier 4, the
    // worst. An unknown memory size is not evidence of a small one.
    const memKnown = !!navigator.deviceMemory;
    if (cores >= 8 && (!memKnown || mem >= 6)) return 2;
    if (cores >= 4 && (!memKnown || mem >= 4)) return 3;
    return 4;
  }

  if (gpuTier === 1 && cores >= 8) return 1;
  if (gpuTier <= 2 && cores >= 4) return 2;
  return 3;
}

function buildTargets() {
  const image = mctx.getImageData(0, 0, mask.width, mask.height).data;
  particles = [];

  const tier = getPerformanceTier();
  perfTier = tier;

  const sampling = tier <= 2 ? 1 : tier === 3 ? 2 : 3;

  swapInterval = tier === 1 ? 150 : tier === 2 ? 250 : tier === 3 ? 500 : 1000;

  const complexityThin = svgComplexity > 10000 ? 0.75 : svgComplexity > 5000 ? 0.88 : 1.0;
  /* Mobile carries a further 25% off the dot count, on top of the sampling
     step. This is the heaviest thing on the page and a phone is where that
     costs the most; the logo reads the same at this density.

     The mobile factors sit OUTSIDE the clamp deliberately. Folded in, they
     land under a Math.min(1.0, ...) that the current logo happens to clear
     (25069 chars, so complexityThin is 0.75) — but a simpler logo pushes the
     product over 1.0, the clamp swallows the difference, and the mobile
     reduction quietly becomes 14% or nothing at all. Out here the 25% is 25%
     whatever the artwork does. */
  const base = Math.min(1.0, (isMobile ? 0.85 : 1.0) * complexityThin * 1.35);
  /* The tier's saving lands here rather than on the frame rate — fewer dots to
     integrate and draw, at full speed, instead of the same dots at half. */
  const T = window.WiehrTier;
  const tierThin = T ? T.pick(1.0, 0.7, 0.45) : 0.7;
  const desktopThin = (isMobile ? base * 0.75 : base) * tierThin;

  for (let y = 0; y < mask.height; y += sampling) {
    for (let x = 0; x < mask.width; x += sampling) {
      const i = (Math.floor(y) * mask.width + Math.floor(x)) * 4;
      if (image[i + 3] > 128) {
        if (Math.random() > desktopThin) continue;
        const logoScale = isMobile ? 0.25 : 0.1875;
        const nx = ((x / mask.width) * 2 - 1) * logoScale;
        const ny = -((y / mask.height) * 2 - 1) * logoScale;
        particles.push(new Particle(nx, ny));
      }
    }
  }

  logoParticleCount = particles.length;
  COUNT = logoParticleCount + networkCount;
  positions = new Float32Array(COUNT * 2);
  venomValues = new Float32Array(COUNT);

  for (let i = 0; i < logoParticleCount; i++) {
    positions[i * 2] = particles[i].x;
    positions[i * 2 + 1] = particles[i].y;
  }
}


const pointSize = '2.0';
const vs = `#version 300 es
precision highp float;
in vec2 position;
in float venom;
void main() {
  gl_Position = vec4(position, 0.0, 1.0);
  gl_PointSize = ${pointSize} + venom * 3.0;
}
`;

const fs = `#version 300 es
precision highp float;
uniform vec3 uColor;
out vec4 outColor;
void main() {
  outColor = vec4(uColor, 1.0);
}
`;


function getParticleColor() {
  const theme = document.documentElement.getAttribute('data-wiehr-theme');
  return theme === 'dark' ? [0.92, 0.92, 0.92] : [0.0, 0.0, 0.0];
}

function compile(type, src) {
  const s = gl.createShader(type);
  gl.shaderSource(s, src);
  gl.compileShader(s);
  if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
    console.error('Shader compilation error:', gl.getShaderInfoLog(s));
    gl.deleteShader(s);
    throw new Error('Shader compilation failed');
  }
  return s;
}


let program, vao;

function initGL() {
  program = gl.createProgram();
  gl.attachShader(program, compile(gl.VERTEX_SHADER, vs));
  gl.attachShader(program, compile(gl.FRAGMENT_SHADER, fs));
  gl.linkProgram(program);

  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
    console.error('Program linking error:', gl.getProgramInfoLog(program));
    throw new Error('Program linking failed');
  }

  gl.useProgram(program);

  gl.enable(gl.BLEND);
  gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);

  vao = gl.createVertexArray();
  gl.bindVertexArray(vao);

  posBuf = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, posBuf);
  gl.bufferData(gl.ARRAY_BUFFER, positions, gl.DYNAMIC_DRAW);

  const loc = gl.getAttribLocation(program, "position");
  gl.enableVertexAttribArray(loc);
  gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);

  venomBuf = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, venomBuf);
  gl.bufferData(gl.ARRAY_BUFFER, venomValues, gl.DYNAMIC_DRAW);

  const venomLoc = gl.getAttribLocation(program, "venom");
  gl.enableVertexAttribArray(venomLoc);
  gl.vertexAttribPointer(venomLoc, 1, gl.FLOAT, false, 0, 0);


  window._wiehrColorLoc = gl.getUniformLocation(program, "uColor");
  const c = getParticleColor();
  gl.uniform3f(window._wiehrColorLoc, c[0], c[1], c[2]);
}


let mouseX = null;
let mouseY = null;
let mouseScreenX = 0;
let mouseScreenY = 0;
let prevMouseX = null;
let prevMouseY = null;
let mouseVelX = 0;
let mouseVelY = 0;
let isVacuum = false;
let perfTier = 2;
let swapInterval = 150;
let lastSwapTime = 0;
let time = 0;
let cursorSize = 0.04;
let cursorSizeTarget = 0.04;
let vacuumStart = 0;
const VACUUM_GROWTH_PER_SEC = 0.55;
const VACUUM_MAX_RADIUS = 3.0;

document.addEventListener('mousemove', (e) => {
  if (window.logoInteractionBlocked) return;
  const rect = canvas.getBoundingClientRect();
  const canvasAspect = canvas.width / canvas.height;

  let newX = ((e.clientX - rect.left) / rect.width) * 2 - 1;
  let newY = -((e.clientY - rect.top) / rect.height) * 2 + 1;

  if (canvasAspect > 1.0) {
    newY /= canvasAspect;
  } else {
    newX *= canvasAspect;
  }

  mouseScreenX = (e.clientX / window.innerWidth) * 2 - 1;
  mouseScreenY = -((e.clientY / window.innerHeight) * 2 - 1);

  if (prevMouseX !== null) {
    mouseVelX = (newX - prevMouseX) * 0.5 + mouseVelX * 0.5;
    mouseVelY = (newY - prevMouseY) * 0.5 + mouseVelY * 0.5;
  }

  prevMouseX = mouseX;
  prevMouseY = mouseY;
  mouseX = newX;
  mouseY = newY;

  const baseSize = 0.04;
  const randomFactor = 0.1 + Math.random() * 0.9;
  cursorSizeTarget = baseSize + (baseSize * 0.5 * randomFactor);
}, {passive: true});

document.addEventListener('mouseleave', () => {
  mouseX = null;
  mouseY = null;
  prevMouseX = null;
  prevMouseY = null;
  mouseVelX = 0;
  mouseVelY = 0;
});

document.addEventListener('mousedown', () => {
  if (window.logoInteractionBlocked) return;
  isVacuum = true;
  vacuumStart = performance.now();
});

document.addEventListener('mouseup', () => {
  isVacuum = false;
  vacuumStart = 0;
});

document.addEventListener('touchstart', (e) => {
  if (window.logoInteractionBlocked) return;
  const rect = canvas.getBoundingClientRect();
  const touch = e.touches[0];
  const canvasAspect = canvas.width / canvas.height;
  let newX = ((touch.clientX - rect.left) / rect.width) * 2 - 1;
  let newY = -((touch.clientY - rect.top) / rect.height) * 2 + 1;
  if (canvasAspect > 1.0) { newY /= canvasAspect; } else { newX *= canvasAspect; }
  prevMouseX = mouseX;
  prevMouseY = mouseY;
  mouseX = newX;
  mouseY = newY;
  mouseScreenX = (touch.clientX / window.innerWidth) * 2 - 1;
  mouseScreenY = -((touch.clientY / window.innerHeight) * 2 - 1);
  isVacuum = true;
  vacuumStart = performance.now();
}, { passive: true });

document.addEventListener('touchmove', (e) => {
  if (window.logoInteractionBlocked) return;
  const rect = canvas.getBoundingClientRect();
  const touch = e.touches[0];
  const canvasAspect = canvas.width / canvas.height;
  let newX = ((touch.clientX - rect.left) / rect.width) * 2 - 1;
  let newY = -((touch.clientY - rect.top) / rect.height) * 2 + 1;
  if (canvasAspect > 1.0) { newY /= canvasAspect; } else { newX *= canvasAspect; }
  if (prevMouseX !== null) {
    mouseVelX = (newX - prevMouseX) * 0.5 + mouseVelX * 0.5;
    mouseVelY = (newY - prevMouseY) * 0.5 + mouseVelY * 0.5;
  }
  prevMouseX = mouseX;
  prevMouseY = mouseY;
  mouseX = newX;
  mouseY = newY;
  mouseScreenX = (touch.clientX / window.innerWidth) * 2 - 1;
  mouseScreenY = -((touch.clientY / window.innerHeight) * 2 - 1);
}, { passive: true });

document.addEventListener('touchend', () => {
  isVacuum = false;
  vacuumStart = 0;
  mouseX = null;
  mouseY = null;
  prevMouseX = null;
  prevMouseY = null;
  mouseVelX = 0;
  mouseVelY = 0;
});


let animationId = null;
let isVisible = true;
let isPaused = false;


if (typeof document.hidden !== "undefined") {
  document.addEventListener("visibilitychange", () => {
    isVisible = !document.hidden;
    if (isVisible && !isPaused && !animationId) {
      render();
    }
  });
}


/* Registered, not assigned. This used to overwrite window.pauseWebGL outright,
   which silently discarded the hook floatingdust.js had already published from
   an earlier <script>. See WiehrLoops in howfastareyou.js. */
if (window.WiehrLoops) {
  window.WiehrLoops.add(
    function () {
      isPaused = true;
      if (animationId) {
        cancelAnimationFrame(animationId);
        animationId = null;
      }
    },
    function () {
      isPaused = false;
      if (isVisible && isLogoSectionVisible && !animationId) {
        render();
      }
    }
  );
}

let lastFrameTime = 0;

/* 60fps ceiling, and deliberately NOT the tier's frame cap.

   Every particle here is integrated per FRAME, not per second — the spring is
   `vx += dx * force; vx *= 0.88; x += vx`, once per render. Frame rate is
   therefore the animation's clock: capping a phone to the tier's 30fps ran the
   whole logo at exactly half speed, which is what "slowmo" was. It was not the
   dot count.

   So the frame budget on this one comes off the density instead (see
   tierThin in buildTargets), which cuts real work per frame without touching
   the speed anything moves at. The 60 ceiling still spares a 144Hz monitor
   from integrating 144 steps a second. */
const FRAME_INTERVAL = 1000 / 60 - 4;

// Allocated once, reused every frame. See the render loop below.
const NO_FORCES = [];
const projectedNetwork = [];
const networkMouseScreen = { x: 0, y: 0 };

function render(timestamp = 0) {
  if (!isVisible || isPaused || !isLogoSectionVisible) {
    animationId = null;
    return;
  }


  if (FRAME_INTERVAL > 0 && timestamp - lastFrameTime < FRAME_INTERVAL) {
    animationId = requestAnimationFrame(render);
    return;
  }
  lastFrameTime = timestamp;

  gl.clearColor(0.0, 0.0, 0.0, 0.0);
  gl.clear(gl.COLOR_BUFFER_BIT);


  if (window._wiehrColorLoc) {
    const c = getParticleColor();
    gl.uniform3f(window._wiehrColorLoc, c[0], c[1], c[2]);
  }

  time += 0.016;

  const rotationY = mouseScreenX * 0.3;
  const rotationX = -mouseScreenY * 0.2;

  cursorSize += (cursorSizeTarget - cursorSize) * 0.1;

  /* Reuse the arrays. `= []` here allocated one array per particle per frame —
     tens of thousands of throwaway objects a second, and the GC pauses that
     buys are exactly the stutter you feel on a phone. */
  for (let i = 0; i < logoParticleCount; i++) {
    particles[i].neighbors.length = 0;
  }

  const neighborCheckProb = perfTier === 1 ? 0.08 : perfTier === 2 ? 0.05 : 0.02;
  const neighborRange = perfTier === 1 ? 18 : perfTier === 2 ? 12 : 6;

  for (let i = 0; i < logoParticleCount; i++) {
    if (Math.random() < neighborCheckProb) {
      for (let j = i + 1; j < Math.min(i + neighborRange, logoParticleCount); j++) {
        const dx = particles[j].x - particles[i].x;
        const dy = particles[j].y - particles[i].y;
        const dist2 = dx * dx + dy * dy;
        if (dist2 < 0.0016) {
          particles[i].neighbors.push(particles[j]);
          particles[j].neighbors.push(particles[i]);
        }
      }
    }
  }

  const mouseX3D = mouseX;
  const mouseY3D = mouseY;

  let vacuumRadius = 0.15;
  if (isVacuum && mouseX3D !== null && mouseY3D !== null) {
    const distFromCenter = Math.sqrt(mouseX3D * mouseX3D + mouseY3D * mouseY3D);
    const logoScale = isMobile ? 0.25 : 0.1875;
    const logoRadius = logoScale * 0.7;

    if (distFromCenter < logoRadius) {
      vacuumRadius = 0.1 + (distFromCenter / logoRadius) * 0.05;
    } else {
      const outsideDist = distFromCenter - logoRadius;
      vacuumRadius = 0.15 + Math.min(outsideDist * 0.8, 0.6);
    }

    if (vacuumStart) {
      const held = (performance.now() - vacuumStart) / 1000;
      vacuumRadius = Math.min(vacuumRadius + held * VACUUM_GROWTH_PER_SEC, VACUUM_MAX_RADIUS);
    }
  }

  /* Everything that is constant for the frame, computed once for the frame.
     canvasAspect was being recomputed inside the loop, and the empty array
     literal allocated one throwaway array per particle per frame. */
  const canvasAspect = canvas.width / canvas.height;
  const cosY = Math.cos(rotationY);
  const sinY = Math.sin(rotationY);
  const cosX = Math.cos(rotationX);
  const sinX = Math.sin(rotationX);

  for (let i = 0; i < logoParticleCount; i++) {
    const pt = particles[i];
    pt.update(mouseX3D, mouseY3D, isVacuum, mouseVelX, mouseVelY, time, NO_FORCES, cursorSize, vacuumRadius);
    pt.projectInto(cosY, sinY, cosX, sinX, canvasAspect, positions, i * 2);
    venomValues[i] = pt.venomStrength;
  }


  /* Published to networkgraph.js through the window, and rebuilt from scratch
     every frame: a new array plus one new object per node. Its consumers read
     it fresh each frame and hold no references across frames, so the array and
     its objects are allocated once and refilled in place instead. */
  window._networkMouseScreen = networkMouseScreen;
  window._networkTime = time;
  networkMouseScreen.x = mouseScreenX;
  networkMouseScreen.y = mouseScreenY;

  if (projectedNetwork.length !== networkCount) {
    projectedNetwork.length = 0;
    for (let i = 0; i < networkCount; i++) {
      projectedNetwork.push({ x: 0, y: 0, isChild: false, parentIdx: 0, country: '', code: '' });
    }
  }

  for (let i = 0; i < networkCount; i++) {
    const np = networkParticles[i];
    np.update(time, mouseScreenX, mouseScreenY);
    const idx = (logoParticleCount + i) * 2;
    positions[idx] = np.x;
    positions[idx + 1] = np.y;

    const slot = projectedNetwork[i];
    slot.x = np.x;
    slot.y = np.y;
    slot.isChild = np._isChild;
    slot.parentIdx = np._parentIdx;
    slot.country = np._country || '';
    slot.code = np._code || '';
  }
  window._networkProjected = projectedNetwork;

  mouseVelX *= 0.95;
  mouseVelY *= 0.95;

  gl.bindBuffer(gl.ARRAY_BUFFER, posBuf);
  gl.bufferSubData(gl.ARRAY_BUFFER, 0, positions);

  gl.bindBuffer(gl.ARRAY_BUFFER, venomBuf);
  gl.bufferSubData(gl.ARRAY_BUFFER, 0, venomValues);

  gl.drawArrays(gl.POINTS, 0, COUNT);
  animationId = requestAnimationFrame(render);
}
