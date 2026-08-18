

'use strict';

const ScrollIndicator = (function() {
    let indicator = null;
    let isVisible = true;
    let hasScrolled = false;

    const CONFIG = {
        fadeOutDelay: 3000,
        animationDuration: 1500
    };

    function init() {
        if (indicator) return;


        const noScrollIndicator = document.querySelector('[data-no-scroll-indicator]');
        if (noScrollIndicator) return;


        const viewportSections = document.querySelectorAll('[data-viewport-sections], .anchor-section, .archive-roadmap-section');
        if (viewportSections.length === 0) return;

        indicator = document.createElement('div');
        indicator.id = 'scroll-indicator';
        indicator.className = 'scroll-indicator';
        indicator.innerHTML = `
            <div class="scroll-indicator-line"></div>
            <span class="scroll-indicator-text">SCROLL</span>
        `;

        const style = document.createElement('style');
        style.textContent = `
            .scroll-indicator {
                position: fixed;
                bottom: calc(var(--bottom-padding, 40px) + 20px);
                left: 50%;
                transform: translateX(-50%);
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 8px;
                z-index: var(--index-priority-medium, 100);
                opacity: 1;
                transition: opacity 0.5s ease, transform 0.5s ease;
                pointer-events: none;
            }

            .scroll-indicator.hidden {
                opacity: 0;
                transform: translateX(-50%) translateY(20px);
            }

            .scroll-indicator-line {
                width: 1px;
                height: 40px;
                background: linear-gradient(to bottom, transparent, currentColor);
                animation: scroll-pulse 1.5s ease-in-out infinite;
            }

            .scroll-indicator-text {
                font-size: var(--font-size-thin, 12px);
                font-weight: var(--font-weight-thin, 100);
                text-transform: uppercase;
                letter-spacing: 0.2em;
                opacity: 0.7;
            }

            @keyframes scroll-pulse {
                0%, 100% {
                    opacity: 0.3;
                    transform: scaleY(0.8);
                }
                50% {
                    opacity: 1;
                    transform: scaleY(1);
                }
            }

            @media (max-width: 640px) {
                .scroll-indicator {
                    bottom: calc(var(--bottom-padding, 40px) + 10px);
                }

                .scroll-indicator-line {
                    height: 30px;
                }

                .scroll-indicator-text {
                    font-size: 10px;
                }
            }
        `;

        document.head.appendChild(style);
        document.body.appendChild(indicator);

        bindEvents();
    }

    function bindEvents() {
        let scrollTimeout;

        const hideOnScroll = () => {
            if (!hasScrolled) {
                hasScrolled = true;
                hide();
            }
        };

        window.addEventListener('wheel', hideOnScroll, { passive: true });
        window.addEventListener('touchmove', hideOnScroll, { passive: true });
        window.addEventListener('keydown', (e) => {
            if (['ArrowDown', 'ArrowUp', 'PageDown', 'PageUp', 'Space'].includes(e.key)) {
                hideOnScroll();
            }
        });

        window.addEventListener('sectionchange', (e) => {
            if (e.detail && e.detail.to !== 0) {
                hide();
            } else if (e.detail && e.detail.to === 0) {
                show();
            }
        });


        const menuObserver = new MutationObserver((mutations) => {
            const menuOverlay = document.querySelector('#whatareyouinterestedin');
            if (menuOverlay) {
                const isMenuOpen = menuOverlay.getAttribute('data-menu-open') === 'true' ||
                                   menuOverlay.classList.contains('active') ||
                                   menuOverlay.style.display !== 'none';
                if (isMenuOpen) {
                    hide();
                }
            }
        });

        const menuOverlay = document.querySelector('#whatareyouinterestedin');
        if (menuOverlay) {
            menuObserver.observe(menuOverlay, { 
                attributes: true, 
                attributeFilter: ['data-menu-open', 'class', 'style'] 
            });
        }


        document.addEventListener('click', (e) => {
            if (e.target.closest('#wehavefollowinginmenu') || e.target.closest('.menu-trigger')) {
                setTimeout(() => {
                    const menuOverlay = document.querySelector('#whatareyouinterestedin');
                    if (menuOverlay && (menuOverlay.getAttribute('data-menu-open') === 'true' ||
                        menuOverlay.classList.contains('active'))) {
                        hide();
                    }
                }, 50);
            }
        });
    }

    function show() {
        if (!indicator) init();
        indicator.classList.remove('hidden');
        isVisible = true;
    }

    function hide() {
        if (!indicator) return;
        indicator.classList.add('hidden');
        isVisible = false;
    }

    function toggle() {
        if (isVisible) {
            hide();
        } else {
            show();
        }
    }

    function destroy() {
        if (indicator && indicator.parentNode) {
            indicator.parentNode.removeChild(indicator);
        }
        indicator = null;
    }


    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        setTimeout(init, 0);
    }

    return {
        init,
        show,
        hide,
        toggle,
        destroy,
        isVisible: () => isVisible
    };
})();

window.ScrollIndicator = ScrollIndicator;

if (typeof module !== 'undefined' && module.exports) {
    module.exports = ScrollIndicator;
}
