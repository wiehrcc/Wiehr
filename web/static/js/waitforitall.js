

(function() {
    'use strict';

    const CONFIG = {
        minDuration: 800,
        maxDuration: 2500,
        fadeOutDuration: 250,
        blockCount: 20,
        particleCount: 600,
        invertAnimationSpeed: 120
    };

    let canvas, ctx;
    let particles = [];
    let progress = 0;
    let animationId;
    let startTime = 0;
    let resourcesLoaded = 0;
    let totalResources = 0;
    let isComplete = false;

    /* The tier is decided once in js/howfastareyou.js, which runs before this
       file. This used to be a fourth private copy of the cores/memory/UA
       guess, and it disagreed with the others: it put every phone in the
       bottom bucket. All that is left here is the density that follows. */
    function detectPerformance() {
        const Tier = window.WiehrTier;
        const name = Tier ? Tier.name : 'mid';

        CONFIG.particleCount = Tier ? Tier.pick(1200, 550, 250) : 550;

        return name === 'mid' ? 'medium' : name;
    }

    class Particle {
        constructor() {
            this.reset();
        }

        reset() {
            this.x = Math.random() * (canvas ? canvas.width : window.innerWidth);
            this.y = Math.random() * (canvas ? canvas.height : window.innerHeight);
            this.size = Math.random() * 2 + 1;
            this.speedX = (Math.random() - 0.5) * 0.3;
            this.speedY = (Math.random() - 0.5) * 0.3;
            this.opacity = Math.random() * 0.4 + 0.1;
            this.fadeSpeed = Math.random() * 0.01 + 0.002;
            this.fadeDir = Math.random() > 0.5 ? 1 : -1;
        }

        update() {
            this.x += this.speedX;
            this.y += this.speedY;
            this.opacity += this.fadeSpeed * this.fadeDir;

            if (this.opacity >= 0.5 || this.opacity <= 0.05) {
                this.fadeDir *= -1;
            }

            if (this.x < 0) this.x = canvas.width;
            if (this.x > canvas.width) this.x = 0;
            if (this.y < 0) this.y = canvas.height;
            if (this.y > canvas.height) this.y = 0;
        }

        draw() {
            ctx.save();
            ctx.globalAlpha = this.opacity;
            ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--color-text')?.trim() || '#151617';
            ctx.fillRect(this.x, this.y, this.size, this.size);
            ctx.restore();
        }
    }

    function initCanvas() {
        canvas = document.getElementById('noisecanvasinloader');
        if (!canvas) return false;

        ctx = canvas.getContext('2d', { alpha: true });
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);
        return true;
    }

    function resizeCanvas() {
        if (!canvas) return;
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }

    function initParticles() {
        particles = [];
        for (let i = 0; i < CONFIG.particleCount; i++) {
            particles.push(new Particle());
        }
    }

    function animateParticles() {
        if (!ctx || !canvas || isComplete) return;

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        particles.forEach(particle => {
            particle.update();
            particle.draw();
        });

        animationId = requestAnimationFrame(animateParticles);
    }

    function updateProgressBar(value) {

        progress = Math.max(0, Math.min(value, 1));

        const percentText = document.getElementById('loadingpercenttext');
        const blocks = document.querySelectorAll('.loading-block');

        if (percentText) {

            const displayPercent = Math.max(0, Math.floor(progress * 100));
            percentText.textContent = displayPercent + '%';
        }


        const filledCount = Math.floor(progress * CONFIG.blockCount);
        blocks.forEach((block, index) => {
            if (index < filledCount) {
                block.classList.add('filled');
            } else {
                block.classList.remove('filled');
            }
        });
    }

    function trackResources() {

        const images = document.querySelectorAll('img');
        const totalImages = images.length;
        let loadedImages = 0;

        if (totalImages > 0) {
            images.forEach(img => {
                if (img.complete) {
                    loadedImages++;
                } else {
                    img.addEventListener('load', () => {
                        loadedImages++;
                        updateImageProgress(loadedImages, totalImages);
                    });
                    img.addEventListener('error', () => {
                        loadedImages++;
                        updateImageProgress(loadedImages, totalImages);
                    });
                }
            });
        }


        const resources = performance.getEntriesByType('resource');
        totalResources = Math.max(resources.length + totalImages, 1);

        const observer = new PerformanceObserver((list) => {
            resourcesLoaded = list.getEntries().length + loadedImages;
            if (totalResources > 0) {
                const resourceProgress = resourcesLoaded / totalResources;
                const elapsed = Date.now() - startTime;
                const timeProgress = Math.min(elapsed / CONFIG.maxDuration, 0.95);
                const blendedProgress = Math.max(resourceProgress * 0.7, timeProgress);
                updateProgressBar(blendedProgress);
            }
        });

        try {
            observer.observe({ entryTypes: ['resource'] });
        } catch (e) {

        }
    }

    function updateImageProgress(loaded, total) {
        if (total > 0 && !isComplete) {
            const imageProgress = loaded / total;
            const elapsed = Date.now() - startTime;
            const timeProgress = Math.min(elapsed / CONFIG.maxDuration, 0.9);
            const blendedProgress = Math.max(imageProgress * 0.8, timeProgress);
            updateProgressBar(blendedProgress);
        }
    }

    function simulateLoading() {
        startTime = Date.now();
        /* A weaker device gets a SHORTER splash, not a longer one.

           This read the other way round — `low` was held on CONFIG.maxDuration,
           2.5 seconds — so the slowest machines sat on the loading screen three
           times as long as the fastest ones and the whole site felt like it was
           lagging before a single page pixel had drawn. The splash is
           decoration; it is the first thing to give up when there is less to
           spend. */
        const performance = detectPerformance();
        const duration = performance === 'low' ? 500 :
                        performance === 'medium' ? CONFIG.minDuration :
                        CONFIG.minDuration + 200;

        function step() {
            if (isComplete) return;

            const elapsed = Date.now() - startTime;

            const rawProgress = Math.max(0, elapsed / duration);

            const smoothProgress = rawProgress * rawProgress * (3 - 2 * rawProgress);
            const clampedProgress = Math.max(0, Math.min(smoothProgress, 1));

            updateProgressBar(clampedProgress);

            if (clampedProgress < 1 && !isComplete) {
                requestAnimationFrame(step);
            } else if (!window._atlasImagesLoading) {
                updateProgressBar(1);
                setTimeout(hideOverlay, 100);
            }
        }

        step();
    }

    function hideOverlay() {
        isComplete = true;
        const overlay = document.getElementById('moneyruinseverythingoverlay');

        if (overlay) {
            overlay.classList.add('fadeout');

            setTimeout(() => {
                overlay.style.display = 'none';
                if (animationId) {
                    cancelAnimationFrame(animationId);
                }
                document.body.classList.remove('loading');
                document.body.classList.add('loaded');
            }, CONFIG.fadeOutDuration);
        }
    }

    function createOverlayHTML() {
        const overlay = document.getElementById('moneyruinseverythingoverlay');
        if (!overlay) return;


        let blocksHTML = '';
        for (let i = 0; i < CONFIG.blockCount; i++) {
            blocksHTML += `<img src="/static/images/entities/loading.svg" alt="Loading" class="loading-block" data-index="${i}" width="24" height="24">`;
        }

        overlay.innerHTML = `
            <canvas id="noisecanvasinloader" class="noisecanvasoverlay"></canvas>
            <img src="/static/images/entities/network.svg" alt="Wiehr" class="loadinglogoisthere" width="120" height="120">
            <p class="statusmessageisimportant">Connecting<span id="loadingdotstext">...</span></p>
            <div class="progressbarisnotworking">
                <div class="asciiprogressbar">
                    <div class="progressrow">
                        <span class="progressbracket">[</span>
                        <div class="progresstrack" id="loadingblockscontainer">
                            ${blocksHTML}
                        </div>
                        <span class="progressbracket">]</span>
                    </div>
                    <span id="loadingpercenttext" class="percentagedisplay">0%</span>
                </div>
            </div>
        `;


        startInvertAnimation();
    }

    let invertAnimationId = null;
    let invertedBlocks = new Set();

    function startInvertAnimation() {
        const blocks = document.querySelectorAll('.loading-block');
        if (blocks.length === 0) return;

        function animateInvert() {
            if (isComplete) {
                if (invertAnimationId) clearInterval(invertAnimationId);

                blocks.forEach(block => {
                    block.classList.add('filled');
                    block.classList.remove('inverting');
                });
                return;
            }


            const targetFilled = Math.floor(progress * CONFIG.blockCount);


            blocks.forEach((block, i) => {
                if (i < targetFilled) {

                    block.classList.add('filled');
                    block.classList.remove('inverting');
                    invertedBlocks.add(i);
                } else {

                    const shouldFlicker = Math.random() < 0.15;
                    if (shouldFlicker) {
                        block.classList.toggle('inverting');
                    }
                }
            });


            if (targetFilled > 2) {
                const numFlickers = Math.floor(Math.random() * 3) + 1;
                for (let i = 0; i < numFlickers; i++) {
                    const randomIdx = Math.floor(Math.random() * targetFilled);
                    if (blocks[randomIdx] && Math.random() < 0.3) {
                        blocks[randomIdx].classList.toggle('inverting');

                        setTimeout(() => {
                            if (blocks[randomIdx]) {
                                blocks[randomIdx].classList.remove('inverting');
                            }
                        }, 80);
                    }
                }
            }
        }

        invertAnimationId = setInterval(animateInvert, CONFIG.invertAnimationSpeed);
    }

    function animateDots() {
        const dotsEl = document.getElementById('loadingdotstext');
        if (!dotsEl || isComplete) return;

        let dots = 0;
        const maxDots = 3;

        setInterval(() => {
            if (isComplete) return;
            dots = (dots + 1) % (maxDots + 1);
            dotsEl.textContent = '.'.repeat(dots || 1);
        }, 400);
    }

    function init() {
        const performance = detectPerformance();
        window.WIEHR_PERFORMANCE = performance;

        createOverlayHTML();

        if (initCanvas()) {
            initParticles();
            animateParticles();
        }

        animateDots();
        trackResources();
        simulateLoading();

        window.addEventListener('load', () => {
            if (!isComplete && !window._atlasImagesLoading) {
                updateProgressBar(1);
                setTimeout(hideOverlay, 100);
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }


    window.LoadingOverlay = {
        show: function() {
            const overlay = document.getElementById('moneyruinseverythingoverlay');
            if (overlay) {
                isComplete = false;
                overlay.style.display = 'flex';
                overlay.classList.remove('fadeout');
                progress = 0;
                updateProgressBar(0);
                if (initCanvas()) {
                    initParticles();
                    animateParticles();
                }
                simulateLoading();
            }
        },
        hide: hideOverlay,
        setProgress: updateProgressBar
    };


    window.LoadingOverlayV2 = window.LoadingOverlay;
})();
