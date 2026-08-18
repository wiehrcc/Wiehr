

'use strict';

const ContentTransition = (function() {
    let canvas = null;
    let ctx = null;
    let animationId = null;
    let isActive = false;
    let intensity = 0;
    let onCompleteCallback = null;
    let targetIntensity = 0;
    let transitionPhase = 'idle'; 
    let glitchOffset = 0;
    let scanlineOffset = 0;

    const CONFIG = {
        pixelSize: 3,
        noiseIntensity: 0.6,
        transitionDuration: 350,
        fadeSpeed: 0.12,
        glitchBands: 8,
        scanlineGap: 4
    };

    function init() {
        if (canvas) return true;

        canvas = document.createElement('canvas');
        canvas.id = 'contentnoisecanvas';
        canvas.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            width: 100vw;
            height: 100vh;
            z-index: 9999;
            pointer-events: none;
            opacity: 0;
            visibility: hidden;
            transition: opacity 0.05s ease;
        `;
        document.body.appendChild(canvas);

        ctx = canvas.getContext('2d', { alpha: true });
        resize();
        window.addEventListener('resize', resize);

        return true;
    }

    function resize() {
        if (!canvas) return;
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }

    function getThemeColors() {
        const theme = document.documentElement.getAttribute('data-wiehr-theme') || 'light';
        if (theme === 'dark') {
            return {
                bg: [21, 22, 23],
                noise: [244, 244, 244]
            };
        }
        return {
            bg: [244, 244, 244],
            noise: [21, 22, 23]
        };
    }

    function renderNoise() {
        if (!ctx || !canvas) return;

        const colors = getThemeColors();
        const width = canvas.width;
        const height = canvas.height;


        ctx.clearRect(0, 0, width, height);


        glitchOffset = (glitchOffset + 1) % 60;
        scanlineOffset = (scanlineOffset + 2) % height;

        const pixelSize = CONFIG.pixelSize;
        const noiseProb = intensity * CONFIG.noiseIntensity;


        const glitchBands = [];
        for (let i = 0; i < CONFIG.glitchBands; i++) {
            if (Math.random() < intensity * 0.7) {
                glitchBands.push({
                    y: Math.floor(Math.random() * height),
                    height: Math.floor(Math.random() * 40 + 10),
                    offset: Math.floor((Math.random() - 0.5) * 60 * intensity)
                });
            }
        }


        ctx.fillStyle = `rgba(${colors.noise.join(',')}, ${intensity * 0.9})`;

        for (let y = 0; y < height; y += pixelSize) {

            let xOffset = 0;
            for (const band of glitchBands) {
                if (y >= band.y && y < band.y + band.height) {
                    xOffset = band.offset;
                    break;
                }
            }


            const isScanline = (y + scanlineOffset) % CONFIG.scanlineGap === 0;
            const scanlineAlpha = isScanline ? 0.3 : 0;

            for (let x = 0; x < width; x += pixelSize) {
                const shouldNoise = Math.random() < noiseProb;
                const shouldBlock = Math.random() < intensity * 0.15;

                if (shouldNoise || shouldBlock || scanlineAlpha > 0) {
                    const drawX = x + xOffset;
                    if (drawX >= 0 && drawX < width) {
                        if (shouldBlock) {

                            const blockW = Math.floor(Math.random() * 20 + 5) * intensity;
                            const blockH = pixelSize * 2;
                            ctx.globalAlpha = intensity * 0.8;
                            ctx.fillRect(drawX, y, blockW, blockH);
                        } else if (shouldNoise) {
                            ctx.globalAlpha = intensity * (0.5 + Math.random() * 0.5);
                            ctx.fillRect(drawX, y, pixelSize, pixelSize);
                        }
                        if (isScanline) {
                            ctx.globalAlpha = scanlineAlpha * intensity;
                            ctx.fillRect(0, y, width, 1);
                        }
                    }
                }
            }
        }


        if (intensity > 0.3) {
            const numRects = Math.floor(intensity * 5);
            for (let i = 0; i < numRects; i++) {
                if (Math.random() < 0.4) {
                    const rectW = Math.random() * width * 0.3;
                    const rectH = Math.random() * 30 + 5;
                    const rectX = Math.random() * width;
                    const rectY = Math.random() * height;
                    ctx.globalAlpha = intensity * 0.4 * Math.random();
                    ctx.fillRect(rectX, rectY, rectW, rectH);
                }
            }
        }

        ctx.globalAlpha = 1;
    }

    function animate() {
        if (!isActive) {
            animationId = null;
            return;
        }


        if (transitionPhase === 'dissolve') {
            intensity += CONFIG.fadeSpeed;
            if (intensity >= targetIntensity) {
                intensity = targetIntensity;
                if (onCompleteCallback) {
                    const cb = onCompleteCallback;
                    onCompleteCallback = null;
                    cb();
                }
            }
        } else if (transitionPhase === 'reconstruct' || transitionPhase === 'fade') {
            intensity -= CONFIG.fadeSpeed;
            if (intensity <= 0) {
                intensity = 0;
                isActive = false;
                canvas.style.opacity = '0';
                canvas.style.visibility = 'hidden';
                transitionPhase = 'idle';
                animationId = null;
                if (onCompleteCallback) {
                    const cb = onCompleteCallback;
                    onCompleteCallback = null;
                    cb();
                }
                return;
            }
        } else if (transitionPhase === 'noise') {

            intensity += CONFIG.fadeSpeed * 0.5;
            if (intensity >= targetIntensity) {
                intensity = targetIntensity;
            }
        }

        renderNoise();
        animationId = requestAnimationFrame(animate);
    }

    function dissolve(element, midCallback) {
        return new Promise((resolve) => {
            if (!init()) {
                if (midCallback) midCallback();
                resolve();
                return;
            }

            isActive = true;
            transitionPhase = 'dissolve';
            targetIntensity = 1;
            intensity = 0;
            canvas.style.visibility = 'visible';
            canvas.style.opacity = '1';

            onCompleteCallback = () => {
                if (midCallback) midCallback();
                resolve();
            };

            animate();
        });
    }

    function reconstruct(element, completeCallback) {
        return new Promise((resolve) => {
            if (!canvas || !isActive) {
                if (completeCallback) completeCallback();
                resolve();
                return;
            }

            transitionPhase = 'reconstruct';
            targetIntensity = 0;

            onCompleteCallback = () => {
                if (completeCallback) completeCallback();
                resolve();
            };


            if (!animationId) {
                animate();
            }
        });
    }

    function cancel() {
        if (animationId) {
            cancelAnimationFrame(animationId);
            animationId = null;
        }
        isActive = false;
        intensity = 0;
        transitionPhase = 'idle';
        if (canvas) {
            canvas.style.opacity = '0';
        }
    }


    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }


    function showNoise(targetIntensityVal = 0.3) {
        if (!init()) return;

        isActive = true;
        transitionPhase = 'noise';
        targetIntensity = targetIntensityVal;
        intensity = 0;
        canvas.style.visibility = 'visible';
        canvas.style.opacity = '1';

        if (!animationId) {
            animate();
        }
    }


    function hideNoise() {
        if (!canvas) return;

        transitionPhase = 'fade';
        targetIntensity = 0;

        if (!animationId) {
            animate();
        }
    }

    return {
        init: init,
        dissolve: dissolve,
        reconstruct: reconstruct,
        cancel: cancel,
        showNoise: showNoise,
        hideNoise: hideNoise,
        isActive: function() { return isActive; }
    };
})();


const TVNoise = (function() {
    let canvas, gl, program;
    let timeUniform, resolutionUniform, intensityUniform;
    let animationId = null;
    let startTime = 0;
    let intensity = 1.0;
    let isActive = false;
    let onCompleteCallback = null;

    const vertexShaderSource = `
        attribute vec2 a_position;
        void main() {
            gl_Position = vec4(a_position, 0.0, 1.0);
        }
    `;

    const fragmentShaderSource = `
        precision mediump float;
        uniform float u_time;
        uniform vec2 u_resolution;
        uniform float u_intensity;

        float random(vec2 st) {
            return fract(sin(dot(st.xy, vec2(12.9898, 78.233))) * 43758.5453123);
        }

        void main() {
            vec2 st = gl_FragCoord.xy / u_resolution.xy;
            float t = u_time * 8.0;
            float n = random(st * t);

            float staticNoise = random(st * 150.0 + t) * 0.6 + 0.4;
            float grain = random(st * u_resolution + t) * 0.1;

            float final = staticNoise + grain;
            final = clamp(final, 0.0, 1.0);

            gl_FragColor = vec4(vec3(final), u_intensity * 0.9);
        }
    `;

    function createShader(gl, type, source) {
        const shader = gl.createShader(type);
        gl.shaderSource(shader, source);
        gl.compileShader(shader);
        if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
            gl.deleteShader(shader);
            return null;
        }
        return shader;
    }

    function createProgram(gl, vs, fs) {
        const prog = gl.createProgram();
        gl.attachShader(prog, vs);
        gl.attachShader(prog, fs);
        gl.linkProgram(prog);
        if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) {
            gl.deleteProgram(prog);
            return null;
        }
        return prog;
    }

    function init() {
        if (canvas) return true;

        canvas = document.createElement('canvas');
        canvas.id = 'tv-noise-canvas';
        canvas.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            z-index: 99999;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.15s ease-out;
        `;
        document.body.appendChild(canvas);

        gl = canvas.getContext('webgl', { alpha: true, premultipliedAlpha: false });
        if (!gl) return false;

        const vs = createShader(gl, gl.VERTEX_SHADER, vertexShaderSource);
        const fs = createShader(gl, gl.FRAGMENT_SHADER, fragmentShaderSource);
        if (!vs || !fs) return false;

        program = createProgram(gl, vs, fs);
        if (!program) return false;

        const positionBuffer = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
        gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([
            -1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1
        ]), gl.STATIC_DRAW);

        const posLoc = gl.getAttribLocation(program, 'a_position');
        gl.enableVertexAttribArray(posLoc);
        gl.vertexAttribPointer(posLoc, 2, gl.FLOAT, false, 0, 0);

        timeUniform = gl.getUniformLocation(program, 'u_time');
        resolutionUniform = gl.getUniformLocation(program, 'u_resolution');
        intensityUniform = gl.getUniformLocation(program, 'u_intensity');

        resize();
        window.addEventListener('resize', resize);

        return true;
    }

    function resize() {
        if (!canvas) return;
        canvas.width = window.innerWidth * window.devicePixelRatio;
        canvas.height = window.innerHeight * window.devicePixelRatio;
        if (gl) gl.viewport(0, 0, canvas.width, canvas.height);
    }

    function render() {
        if (!gl || !isActive) return;

        const elapsed = (performance.now() - startTime) / 1000;

        gl.clearColor(0, 0, 0, 0);
        gl.clear(gl.COLOR_BUFFER_BIT);
        gl.enable(gl.BLEND);
        gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);

        gl.useProgram(program);
        gl.uniform1f(timeUniform, elapsed);
        gl.uniform2f(resolutionUniform, canvas.width, canvas.height);
        gl.uniform1f(intensityUniform, intensity);

        gl.drawArrays(gl.TRIANGLES, 0, 6);
        animationId = requestAnimationFrame(render);
    }

    function show(duration, callback) {
        if (!init()) {
            if (callback) callback();
            return;
        }

        onCompleteCallback = callback;
        isActive = true;
        startTime = performance.now();
        intensity = 1.0;
        canvas.style.opacity = '1';
        canvas.style.pointerEvents = 'all';

        render();

        if (duration && duration > 0) {
            setTimeout(hide, duration);
        }
    }

    function hide(callback) {
        if (!canvas) return;

        const fadeOut = () => {
            intensity -= 0.06;
            if (intensity <= 0) {
                intensity = 0;
                isActive = false;
                canvas.style.opacity = '0';
                canvas.style.pointerEvents = 'none';
                if (animationId) {
                    cancelAnimationFrame(animationId);
                    animationId = null;
                }
                if (onCompleteCallback) {
                    onCompleteCallback();
                    onCompleteCallback = null;
                }
                if (callback) callback();
            } else {
                requestAnimationFrame(fadeOut);
            }
        };
        fadeOut();
    }

    function transition(url, duration) {
        duration = duration || 400;
        show(null, null);
        setTimeout(() => {
            window.location.href = url;
        }, duration / 2);
    }

    return {
        init: init,
        show: show,
        hide: hide,
        transition: transition,
        isActive: function() { return isActive; }
    };
})();


window.ContentTransition = ContentTransition;
window.TVNoise = TVNoise;

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ContentTransition, TVNoise };
}
