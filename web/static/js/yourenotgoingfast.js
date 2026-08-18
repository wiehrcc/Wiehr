'use strict';

const PageTransitions = (function() {
    let initialized = false;
    let transitionDuration = 400;
    let useWebGL = true;

    function init(options) {
        if (initialized) return;

        options = options || {};
        transitionDuration = options.duration || 400;
        useWebGL = options.webgl !== false;

        if (useWebGL && typeof TVNoise !== 'undefined') {
            TVNoise.init();
        }

        attachLinkHandlers();
        handlePopState();
        initialized = true;
    }

    function attachLinkHandlers() {
        document.addEventListener('click', function(e) {
            const link = e.target.closest('a[href]');
            if (!link) return;

            const href = link.getAttribute('href');
            if (!shouldIntercept(link, href)) return;

            e.preventDefault();
            navigateTo(href);
        });
    }

    function shouldIntercept(link, href) {
        if (!href) return false;
        if (href.startsWith('#')) return false;
        if (href.startsWith('javascript:')) return false;
        if (href.startsWith('mailto:')) return false;
        if (href.startsWith('tel:')) return false;
        if (link.target === '_blank') return false;
        if (link.hasAttribute('download')) return false;
        if (link.classList.contains('no-transition')) return false;
        if (link.dataset.noTransition === 'true') return false;

        try {
            const url = new URL(href, window.location.origin);
            if (url.origin !== window.location.origin) return false;

            if (url.pathname === window.location.pathname && url.hash) return false;
        } catch (e) {
            return false;
        }

        return true;
    }

    function navigateTo(url, options) {
        options = options || {};
        const duration = options.duration || transitionDuration;

        if (useWebGL && typeof TVNoise !== 'undefined') {
            TVNoise.transition(url, duration);
        } else {
            fallbackTransition(url, duration);
        }
    }

    function fallbackTransition(url, duration) {
        const overlay = document.createElement('div');
        overlay.className = 'systemisrigged';
        overlay.style.cssText = `
            position: fixed;
            inset: 0;
            z-index: 9999;
            background: var(--color-bg, #000);
            opacity: 0;
            transition: opacity ${duration / 2}ms ease-out;
        `;
        document.body.appendChild(overlay);

        requestAnimationFrame(() => {
            overlay.style.opacity = '1';
        });

        setTimeout(() => {
            window.location.href = url;
        }, duration / 2);
    }

    function handlePopState() {
        window.addEventListener('popstate', function(e) {
            if (typeof TVNoise !== 'undefined' && TVNoise.isActive && TVNoise.isActive()) {
                TVNoise.hide();
            }
            if (typeof ContentTransition !== 'undefined' && ContentTransition.isActive && ContentTransition.isActive()) {
                ContentTransition.cancel();
            }
        });
    }

    function setDuration(ms) {
        transitionDuration = ms;
    }

    function setWebGL(enabled) {
        useWebGL = enabled;
    }

    return {
        init: init,
        navigateTo: navigateTo,
        setDuration: setDuration,
        setWebGL: setWebGL
    };
})();

document.addEventListener('DOMContentLoaded', function() {
    PageTransitions.init();
});
