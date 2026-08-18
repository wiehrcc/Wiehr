

'use strict';

const NoiseBorder = (function() {
    let canvas = null;
    let ctx = null;
    let animationId = null;
    let activeElements = new Map();
    let isInitialized = false;
    let particles = [];

    const CONFIG = {
        particleCount: 80,
        particleSize: 1.5,
        particleSpeed: 2,
        borderPadding: 3,
        fadeInSpeed: 0.15,
        fadeOutSpeed: 0.1,
        particleLifeVariance: 0.3,
        spawnRate: 0.4
    };

    class Particle {
        constructor(rect, side) {
            this.rect = rect;
            this.side = side;
            this.reset();
        }

        reset() {
            const r = this.rect;
            const padding = CONFIG.borderPadding;

            switch(this.side) {
                case 'top':
                    this.x = r.left + Math.random() * r.width;
                    this.y = r.top - padding;
                    this.vx = (Math.random() - 0.5) * CONFIG.particleSpeed;
                    this.vy = (Math.random() - 0.5) * CONFIG.particleSpeed * 0.3;
                    break;
                case 'bottom':
                    this.x = r.left + Math.random() * r.width;
                    this.y = r.bottom + padding;
                    this.vx = (Math.random() - 0.5) * CONFIG.particleSpeed;
                    this.vy = (Math.random() - 0.5) * CONFIG.particleSpeed * 0.3;
                    break;
                case 'left':
                    this.x = r.left - padding;
                    this.y = r.top + Math.random() * r.height;
                    this.vx = (Math.random() - 0.5) * CONFIG.particleSpeed * 0.3;
                    this.vy = (Math.random() - 0.5) * CONFIG.particleSpeed;
                    break;
                case 'right':
                    this.x = r.right + padding;
                    this.y = r.top + Math.random() * r.height;
                    this.vx = (Math.random() - 0.5) * CONFIG.particleSpeed * 0.3;
                    this.vy = (Math.random() - 0.5) * CONFIG.particleSpeed;
                    break;
            }

            this.life = 1;
            this.decay = 0.01 + Math.random() * CONFIG.particleLifeVariance * 0.02;
            this.size = CONFIG.particleSize * (0.5 + Math.random() * 0.5);
            this.alpha = 0.3 + Math.random() * 0.5;
        }

        update() {
            this.x += this.vx;
            this.y += this.vy;
            this.life -= this.decay;


            const r = this.rect;
            const centerX = r.left + r.width / 2;
            const centerY = r.top + r.height / 2;


            if (this.side === 'top' || this.side === 'bottom') {
                const targetY = this.side === 'top' ? r.top : r.bottom;
                this.vy += (targetY - this.y) * 0.002;
            } else {
                const targetX = this.side === 'left' ? r.left : r.right;
                this.vx += (targetX - this.x) * 0.002;
            }


            this.vx *= 0.98;
            this.vy *= 0.98;
        }

        draw(ctx) {
            if (this.life <= 0) return;

            const alpha = this.alpha * this.life;
            ctx.fillStyle = `rgba(0, 0, 0, ${alpha})`;
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fill();
        }

        isAlive() {
            return this.life > 0;
        }
    }

    function init() {
        if (isInitialized) return;
        isInitialized = true;

        canvas = document.createElement('canvas');
        canvas.id = 'noise-border-canvas';
        canvas.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 99998;
        `;
        document.body.appendChild(canvas);
        ctx = canvas.getContext('2d');

        resize();
        window.addEventListener('resize', resize);

        initAll();
    }

    function resize() {
        if (!canvas) return;
        const dpr = window.devicePixelRatio || 1;
        canvas.width = window.innerWidth * dpr;
        canvas.height = window.innerHeight * dpr;
        canvas.style.width = window.innerWidth + 'px';
        canvas.style.height = window.innerHeight + 'px';
        ctx.scale(dpr, dpr);
    }

    function spawnParticles(element, rect) {
        const data = activeElements.get(element);
        if (!data) return;

        const sides = ['top', 'bottom', 'left', 'right'];
        const particlesPerSide = Math.floor(CONFIG.particleCount / 4);

        sides.forEach(side => {
            if (Math.random() < CONFIG.spawnRate) {
                data.particles.push(new Particle(rect, side));
            }
        });


        if (data.particles.length > CONFIG.particleCount * 2) {
            data.particles = data.particles.filter(p => p.isAlive());
        }
    }

    function animate() {
        if (activeElements.size === 0 && particles.length === 0) {
            animationId = null;
            return;
        }

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        activeElements.forEach((data, element) => {
            const rect = element.getBoundingClientRect();


            if (data.active) {
                data.opacity = Math.min(1, data.opacity + CONFIG.fadeInSpeed);
            } else {
                data.opacity = Math.max(0, data.opacity - CONFIG.fadeOutSpeed);
            }

            if (data.opacity <= 0) {
                activeElements.delete(element);
                return;
            }


            spawnParticles(element, rect);


            ctx.globalAlpha = data.opacity;
            data.particles.forEach(p => {
                p.rect = rect;
                p.update();
                p.draw(ctx);
            });


            data.particles = data.particles.filter(p => p.isAlive());
        });

        ctx.globalAlpha = 1;
        animationId = requestAnimationFrame(animate);
    }

    function addElement(element) {
        if (!activeElements.has(element)) {
            activeElements.set(element, {
                active: true,
                opacity: 0,
                particles: []
            });
        } else {
            activeElements.get(element).active = true;
        }

        if (!animationId) {
            animate();
        }
    }

    function removeElement(element) {
        const data = activeElements.get(element);
        if (data) {
            data.active = false;
        }
    }

    function bindElement(element) {
        element.addEventListener('mouseenter', () => addElement(element));
        element.addEventListener('mouseleave', () => removeElement(element));
        element.classList.add('noise-border-bound');
    }

    function initAll(selector = '[data-noise-border], .noise-border-hover') {
        const elements = document.querySelectorAll(selector);
        elements.forEach(el => {
            if (!el.classList.contains('noise-border-bound')) {
                bindElement(el);
            }
        });
    }

    function destroy() {
        if (animationId) {
            cancelAnimationFrame(animationId);
        }
        if (canvas && canvas.parentNode) {
            canvas.parentNode.removeChild(canvas);
        }
        activeElements.clear();
        particles = [];
        isInitialized = false;
    }


    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        setTimeout(init, 0);
    }

    return {
        init,
        bindElement,
        initAll,
        addElement,
        removeElement,
        destroy,
        CONFIG
    };
})();

window.NoiseBorder = NoiseBorder;

if (typeof module !== 'undefined' && module.exports) {
    module.exports = NoiseBorder;
}
