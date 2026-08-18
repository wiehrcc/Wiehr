(function() {
    'use strict';

    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) || window.innerWidth <= 640;
    const cores = navigator.hardwareConcurrency || 4;
    const mem = navigator.deviceMemory || 4;
    const COUNT = isMobile ? 40 : (cores >= 8 && mem >= 8 ? 140 : 90);

    let canvas, ctx;
    let particles = [];
    let animationId = null;
    let isVisible = !document.hidden;

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

    function animate() {
        if (!isVisible) { animationId = null; return; }
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        const color = getComputedStyle(document.documentElement).getPropertyValue('--color-text')?.trim() || '#151617';
        ctx.fillStyle = color;
        for (let i = 0; i < particles.length; i++) {
            particles[i].update();
            particles[i].draw(color);
        }
        ctx.globalAlpha = 1;
        animationId = requestAnimationFrame(animate);
    }

    function init() {
        canvas = document.getElementById('floatingdustcanvas');
        if (!canvas) return;
        ctx = canvas.getContext('2d', { alpha: true });
        resize();
        window.addEventListener('resize', resize);

        for (let i = 0; i < COUNT; i++) particles.push(new DustPixel());

        document.addEventListener('visibilitychange', function() {
            isVisible = !document.hidden;
            if (isVisible && !animationId) animate();
        });

        animate();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
