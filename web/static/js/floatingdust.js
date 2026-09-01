(function() {
    'use strict';

    // Density and frame rate both come from the shared tier (js/howfastareyou.js)
    // rather than a third private copy of the cores/memory/user-agent guess.
    const Tier = window.WiehrTier;
    const COUNT = Tier ? Tier.pick(140, 70, 30) : 90;

    let canvas, ctx;
    let particles = [];
    let stopFrames = null;

    class DustPixel {
        constructor() {
            this.reset();
        }
        reset() {
            this.x = Math.random() * (canvas ? canvas.width : window.innerWidth);
            this.y = Math.random() * (canvas ? canvas.height : window.innerHeight);
            this.size = Math.random() * 2 + 1;
            this.speedX = (Math.random() - 0.5) * 0.15;
            this.speedY = (Math.random() - 0.5) * 0.15;
            this.opacity = Math.random() * 0.25 + 0.05;
            this.fadeSpeed = Math.random() * 0.006 + 0.001;
            this.fadeDir = Math.random() > 0.5 ? 1 : -1;
        }
        update() {
            this.x += this.speedX;
            this.y += this.speedY;
            this.opacity += this.fadeSpeed * this.fadeDir;
            if (this.opacity >= 0.3 || this.opacity <= 0.03) this.fadeDir *= -1;
            if (this.x < 0) this.x = canvas.width;
            if (this.x > canvas.width) this.x = 0;
            if (this.y < 0) this.y = canvas.height;
            if (this.y > canvas.height) this.y = 0;
        }
        draw(color) {
            ctx.globalAlpha = this.opacity;
            ctx.fillRect(this.x, this.y, this.size, this.size);
        }
    }

    function resize() {
        if (!canvas) return;
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }

    // Read once per frame instead of once per frame *per particle* — this used
    // to call getComputedStyle on every tick, which forces a style recalc.
    let inkColor = null;
    function readInk() {
        inkColor = getComputedStyle(document.documentElement)
            .getPropertyValue('--color-text')?.trim() || '#151617';
    }

    function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = inkColor;
        for (let i = 0; i < particles.length; i++) {
            particles[i].update();
            particles[i].draw(inkColor);
        }
        ctx.globalAlpha = 1;
    }

    function init() {
        canvas = document.getElementById('floatingdustcanvas');
        if (!canvas) return;
        ctx = canvas.getContext('2d', { alpha: true });
        resize();
        window.addEventListener('resize', resize);

        for (let i = 0; i < COUNT; i++) particles.push(new DustPixel());

        readInk();
        // The theme toggle changes --color-text; nothing else does.
        new MutationObserver(readInk).observe(document.documentElement, {
            attributes: true, attributeFilter: ['data-wiehr-theme']
        });

        // Tier.frame caps the rate and stops the loop while the tab is hidden.
        stopFrames = Tier ? Tier.frame(draw) : (function () {
            let id = null;
            (function loop() { draw(); id = requestAnimationFrame(loop); })();
            return function () { if (id) cancelAnimationFrame(id); };
        })();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
