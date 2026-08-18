

'use strict';

const Depth3D = (function() {
    const instances = new Map();
    let globalMouseX = 0;
    let globalMouseY = 0;
    let isMouseTracking = false;

    const CONFIG = {
        maxTilt: 15,
        smoothing: 0.08,
        perspective: 800
    };

    function initGlobalMouseTracking() {
        if (isMouseTracking) return;
        isMouseTracking = true;

        document.addEventListener('mousemove', (e) => {
            globalMouseX = (e.clientX / window.innerWidth) * 2 - 1;
            globalMouseY = (e.clientY / window.innerHeight) * 2 - 1;
        });
    }

    class Depth3DInstance {
        constructor(container, options = {}) {
            this.container = container;
            this.options = {
                maxTilt: options.maxTilt || CONFIG.maxTilt,
                smoothing: options.smoothing || CONFIG.smoothing,
                perspective: options.perspective || CONFIG.perspective,
                onClick: options.onClick || null,
                imageSrc: options.imageSrc || null
            };

            this.currentRotateX = 0;
            this.currentRotateY = 0;
            this.targetRotateX = 0;
            this.targetRotateY = 0;
            this.isHovered = false;
            this.isVisible = true;
            this.animationId = null;

            this.init();
        }

        init() {
            initGlobalMouseTracking();
            this.setupContainer();
            this.bindEvents();
            this.animate();
        }

        setupContainer() {

            this.container.style.perspective = this.options.perspective + 'px';
            this.container.style.perspectiveOrigin = 'center center';


            let inner = this.container.querySelector('.depth3d-inner');
            if (!inner) {

                inner = document.createElement('div');
                inner.className = 'depth3d-inner';
                while (this.container.firstChild) {
                    inner.appendChild(this.container.firstChild);
                }
                this.container.appendChild(inner);
            }
            this.inner = inner;


            this.inner.style.transformStyle = 'preserve-3d';
            this.inner.style.transition = 'transform 0.1s ease-out';
            this.inner.style.willChange = 'transform';


            this.img = this.inner.querySelector('img');
            if (this.img) {
                this.img.style.display = 'block';
                this.img.style.width = '100%';
                this.img.style.height = '100%';
                this.img.style.objectFit = 'contain';
            }
        }

        bindEvents() {
            this.container.addEventListener('mouseenter', () => {
                this.isHovered = true;
            });

            this.container.addEventListener('mouseleave', () => {
                this.isHovered = false;
                this.targetRotateX = 0;
                this.targetRotateY = 0;
            });

            this.container.addEventListener('mousemove', (e) => {
                if (!this.isHovered) return;

                const rect = this.container.getBoundingClientRect();
                const x = (e.clientX - rect.left) / rect.width;
                const y = (e.clientY - rect.top) / rect.height;

                this.targetRotateY = (x - 0.5) * this.options.maxTilt * 2;
                this.targetRotateX = -(y - 0.5) * this.options.maxTilt * 2;
            });

            if (this.options.onClick) {
                this.container.style.cursor = 'pointer';
                this.container.addEventListener('click', (e) => {
                    this.options.onClick(e, this);
                });
            }


            const intersectionObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    this.isVisible = entry.isIntersecting;
                    if (this.isVisible && !this.animationId) {
                        this.animate();
                    }
                });
            }, { threshold: 0.1 });
            intersectionObserver.observe(this.container);
        }

        animate() {
            if (!this.isVisible) {
                this.animationId = null;
                return;
            }


            if (!this.isHovered) {
                this.targetRotateY = globalMouseX * this.options.maxTilt * 0.3;
                this.targetRotateX = -globalMouseY * this.options.maxTilt * 0.3;
            }


            this.currentRotateX += (this.targetRotateX - this.currentRotateX) * this.options.smoothing;
            this.currentRotateY += (this.targetRotateY - this.currentRotateY) * this.options.smoothing;


            if (this.inner) {
                this.inner.style.transform = `rotateX(${this.currentRotateX}deg) rotateY(${this.currentRotateY}deg)`;
            }

            this.animationId = requestAnimationFrame(() => this.animate());
        }

        destroy() {
            if (this.animationId) {
                cancelAnimationFrame(this.animationId);
            }
            instances.delete(this.container);
        }

        reset() {
            this.targetRotateX = 0;
            this.targetRotateY = 0;
        }
    }

    function create(container, options) {
        const instance = new Depth3DInstance(container, options);
        instances.set(instance.container, instance);
        return instance;
    }

    function get(container) {
        const el = typeof container === 'string' ? document.querySelector(container) : container;
        return instances.get(el);
    }

    function destroyAll() {
        instances.forEach(instance => instance.destroy());
        instances.clear();
    }

    function initAll(selector = '[data-depth3d]') {
        const elements = document.querySelectorAll(selector);
        elements.forEach(el => {
            if (instances.has(el)) return; 

            const options = {
                imageSrc: el.dataset.depth3dSrc || null,
                maxTilt: parseFloat(el.dataset.depth3dTilt) || CONFIG.maxTilt,
                onClick: el.dataset.depth3dHref ? () => {
                    window.location.href = el.dataset.depth3dHref;
                } : null
            };
            create(el, options);
        });
    }


    window.addEventListener('sectionchange', () => {
        setTimeout(initAll, 100);
    });

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => initAll());
    } else {
        setTimeout(initAll, 0);
    }

    return {
        create,
        get,
        destroyAll,
        initAll,
        CONFIG
    };
})();

window.Depth3D = Depth3D;

if (typeof module !== 'undefined' && module.exports) {
    module.exports = Depth3D;
}
