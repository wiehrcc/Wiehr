

(function() {
    'use strict';

    let canvas = null;
    let gl = null;
    let program = null;
    let animationId = null;
    let particles = [];
    let startTime = 0;
    let isAnimating = false;


    const vertexShaderSource = `
        attribute vec2 a_position;
        attribute vec2 a_velocity;
        attribute float a_size;
        attribute float a_opacity;

        uniform vec2 u_resolution;
        uniform float u_time;
        uniform float u_progress;
        uniform int u_mode;

        varying float v_opacity;

        void main() {
            vec2 position = a_position;

            if (u_mode == 0) {
                position += a_velocity * u_progress;
                v_opacity = 1.0 - u_progress;
            } else {
                position += a_velocity * (1.0 - u_progress);
                v_opacity = u_progress;
            }

            vec2 clipSpace = (position / u_resolution) * 2.0 - 1.0;
            clipSpace.y *= -1.0;

            gl_Position = vec4(clipSpace, 0.0, 1.0);
            gl_PointSize = a_size * (0.5 + v_opacity * 0.5);
        }
    `;


    const fragmentShaderSource = `
        precision mediump float;

        uniform vec3 u_color;
        varying float v_opacity;

        void main() {
            gl_FragColor = vec4(u_color, v_opacity);
        }
    `;


    function initWebGL() {
        canvas = document.getElementById('menu-webgl-canvas');
        if (!canvas) {
            canvas = document.createElement('canvas');
            canvas.id = 'menu-webgl-canvas';
            canvas.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                pointer-events: none;
                z-index: var(--index-priority-medium, 100);
                opacity: 0;
                transition: opacity 0.2s ease;
            `;
            document.body.appendChild(canvas);
        }

        gl = canvas.getContext('webgl', { alpha: true, premultipliedAlpha: false });
        if (!gl) {
            console.error('WebGL not supported');
            return false;
        }


        const vertexShader = createShader(gl.VERTEX_SHADER, vertexShaderSource);
        const fragmentShader = createShader(gl.FRAGMENT_SHADER, fragmentShaderSource);

        if (!vertexShader || !fragmentShader) return false;


        program = createProgram(vertexShader, fragmentShader);
        if (!program) return false;

        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);

        return true;
    }

    function createShader(type, source) {
        const shader = gl.createShader(type);
        gl.shaderSource(shader, source);
        gl.compileShader(shader);

        if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
            console.error('Shader compile error:', gl.getShaderInfoLog(shader));
            gl.deleteShader(shader);
            return null;
        }

        return shader;
    }

    function createProgram(vertexShader, fragmentShader) {
        const prog = gl.createProgram();
        gl.attachShader(prog, vertexShader);
        gl.attachShader(prog, fragmentShader);
        gl.linkProgram(prog);

        if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) {
            console.error('Program link error:', gl.getProgramInfoLog(prog));
            return null;
        }

        return prog;
    }

    function resizeCanvas() {
        if (!canvas) return;
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        if (gl) {
            gl.viewport(0, 0, canvas.width, canvas.height);
        }
    }


    function sampleContent(element) {
        if (!element) return [];

        const particles = [];
        const rect = element.getBoundingClientRect();
        const visibleElements = element.querySelectorAll('*');


        const computedStyle = getComputedStyle(document.documentElement);
        const textColor = computedStyle.getPropertyValue('--color-text')?.trim() || '#151617';

        visibleElements.forEach(el => {
            const elRect = el.getBoundingClientRect();

            if (elRect.width < 2 || elRect.height < 2) return;

            const elStyle = getComputedStyle(el);
            if (elStyle.opacity === '0' || elStyle.visibility === 'hidden') return;


            const density = Math.max(1, Math.floor((elRect.width * elRect.height) / 800));

            for (let i = 0; i < density; i++) {
                const x = elRect.left + Math.random() * elRect.width;
                const y = elRect.top + Math.random() * elRect.height;

                particles.push({
                    x: x,
                    y: y,
                    vx: (Math.random() - 0.5) * 400,
                    vy: (Math.random() - 0.5) * 400,
                    size: 3 + Math.random() * 2,
                    opacity: 1
                });
            }
        });


        const fillCount = Math.floor((canvas.width * canvas.height) / 3000);
        for (let i = 0; i < fillCount; i++) {
            if (Math.random() > 0.4) continue;
            particles.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                vx: (Math.random() - 0.5) * 400,
                vy: (Math.random() - 0.5) * 400,
                size: 2 + Math.random() * 2,
                opacity: 1
            });
        }

        return particles;
    }


    function render(mode, progress) {
        if (!gl || !program || particles.length === 0) return;

        gl.clearColor(0, 0, 0, 0);
        gl.clear(gl.COLOR_BUFFER_BIT);

        gl.enable(gl.BLEND);
        gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);

        gl.useProgram(program);


        const positions = new Float32Array(particles.length * 2);
        const velocities = new Float32Array(particles.length * 2);
        const sizes = new Float32Array(particles.length);
        const opacities = new Float32Array(particles.length);

        particles.forEach((p, i) => {
            positions[i * 2] = p.x;
            positions[i * 2 + 1] = p.y;
            velocities[i * 2] = p.vx;
            velocities[i * 2 + 1] = p.vy;
            sizes[i] = p.size;
            opacities[i] = p.opacity;
        });


        const positionLoc = gl.getAttribLocation(program, 'a_position');
        const positionBuffer = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
        gl.bufferData(gl.ARRAY_BUFFER, positions, gl.STATIC_DRAW);
        gl.enableVertexAttribArray(positionLoc);
        gl.vertexAttribPointer(positionLoc, 2, gl.FLOAT, false, 0, 0);

        const velocityLoc = gl.getAttribLocation(program, 'a_velocity');
        const velocityBuffer = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, velocityBuffer);
        gl.bufferData(gl.ARRAY_BUFFER, velocities, gl.STATIC_DRAW);
        gl.enableVertexAttribArray(velocityLoc);
        gl.vertexAttribPointer(velocityLoc, 2, gl.FLOAT, false, 0, 0);

        const sizeLoc = gl.getAttribLocation(program, 'a_size');
        const sizeBuffer = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, sizeBuffer);
        gl.bufferData(gl.ARRAY_BUFFER, sizes, gl.STATIC_DRAW);
        gl.enableVertexAttribArray(sizeLoc);
        gl.vertexAttribPointer(sizeLoc, 1, gl.FLOAT, false, 0, 0);

        const opacityLoc = gl.getAttribLocation(program, 'a_opacity');
        const opacityBuffer = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, opacityBuffer);
        gl.bufferData(gl.ARRAY_BUFFER, opacities, gl.STATIC_DRAW);
        gl.enableVertexAttribArray(opacityLoc);
        gl.vertexAttribPointer(opacityLoc, 1, gl.FLOAT, false, 0, 0);


        const resolutionLoc = gl.getUniformLocation(program, 'u_resolution');
        gl.uniform2f(resolutionLoc, canvas.width, canvas.height);

        const progressLoc = gl.getUniformLocation(program, 'u_progress');
        gl.uniform1f(progressLoc, progress);

        const modeLoc = gl.getUniformLocation(program, 'u_mode');
        gl.uniform1i(modeLoc, mode);


        const computedStyle = getComputedStyle(document.documentElement);
        const textColor = computedStyle.getPropertyValue('--color-text')?.trim() || '#151617';
        const rgb = hexToRgb(textColor);
        const colorLoc = gl.getUniformLocation(program, 'u_color');
        gl.uniform3f(colorLoc, rgb.r, rgb.g, rgb.b);


        gl.drawArrays(gl.POINTS, 0, particles.length);


        gl.deleteBuffer(positionBuffer);
        gl.deleteBuffer(velocityBuffer);
        gl.deleteBuffer(sizeBuffer);
        gl.deleteBuffer(opacityBuffer);
    }

    function hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16) / 255,
            g: parseInt(result[2], 16) / 255,
            b: parseInt(result[3], 16) / 255
        } : { r: 0.08, g: 0.09, b: 0.09 };
    }


    function easeInOutCubic(t) {
        return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
    }


    function animate(timestamp) {
        const elapsed = timestamp - startTime;
        const duration = 800;
        let progress = Math.min(elapsed / duration, 1);
        progress = easeInOutCubic(progress);

        const mode = isAnimating === 'dissolve' ? 0 : 1;
        render(mode, progress);

        if (progress < 1) {
            animationId = requestAnimationFrame(animate);
        } else {
            canvas.style.opacity = '0';
            isAnimating = false;
            if (window.MenuWebGL.onComplete) {
                window.MenuWebGL.onComplete();
                window.MenuWebGL.onComplete = null;
            }
        }
    }


    window.MenuWebGL = {
        init: function() {
            return initWebGL();
        },

        dissolve: function(element, callback) {
            if (isAnimating) return;

            particles = sampleContent(element);
            if (particles.length === 0) {
                if (callback) callback();
                return;
            }

            isAnimating = 'dissolve';
            canvas.style.opacity = '1';
            startTime = performance.now();
            this.onComplete = callback;
            animationId = requestAnimationFrame(animate);
        },

        reconstruct: function(element, callback) {
            if (isAnimating) return;

            particles = sampleContent(element);
            if (particles.length === 0) {
                if (callback) callback();
                return;
            }

            isAnimating = 'reconstruct';
            canvas.style.opacity = '1';
            startTime = performance.now();
            this.onComplete = callback;
            animationId = requestAnimationFrame(animate);
        },

        cancel: function() {
            if (animationId) {
                cancelAnimationFrame(animationId);
                animationId = null;
            }
            isAnimating = false;
            if (canvas) canvas.style.opacity = '0';
        },

        onComplete: null
    };


    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => window.MenuWebGL.init());
    } else {
        window.MenuWebGL.init();
    }
})();
