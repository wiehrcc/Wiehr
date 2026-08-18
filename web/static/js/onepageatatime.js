
(function() {
    'use strict';

    var CONFIG = {
        transitionDuration: 240,
        scrollCooldown: 300,
        scrollThreshold: 30
    };

    function initOne(container) {
        var slices = Array.prototype.slice.call(container.children).filter(function(el) {
            return el.classList.contains('pageslice');
        });
        if (slices.length <= 1) return;

        slices.forEach(function(slice, i) {
            slice.style.display = i === 0 ? '' : 'none';
        });

        var current = 0;
        var transitioning = false;
        var lastMoveTime = 0;
        var accumulatedDelta = 0;
        var scrollTimeout = null;
        var touchStartY = 0;
        var touchStartTime = 0;

        var flipper = window.SectionFlipper.createNav(slices.length, {
            initial: 0,
            ariaLabel: 'Pages',
            onSelect: function(index) { goTo(index); }
        });

        function goTo(index) {
            if (transitioning || index === current || index < 0 || index >= slices.length) return;

            var now = Date.now();
            if (now - lastMoveTime < CONFIG.scrollCooldown) return;

            transitioning = true;
            lastMoveTime = now;

            if (window.triggerGlitch) window.triggerGlitch(150);

            var from = slices[current];
            var to = slices[index];

            from.style.transition = 'opacity ' + (CONFIG.transitionDuration / 2) + 'ms ease-out';
            from.style.opacity = '0';

            setTimeout(function() {
                from.style.display = 'none';
                to.style.display = '';
                to.style.opacity = '0';
                to.style.transition = 'opacity ' + (CONFIG.transitionDuration / 2) + 'ms ease-in';
                void to.offsetHeight;
                to.style.opacity = '1';

                current = index;
                flipper.setActive(current);

                setTimeout(function() { transitioning = false; }, CONFIG.transitionDuration / 2);
            }, CONFIG.transitionDuration / 2);
        }

        function handleWheel(e) {
            if (transitioning) { e.preventDefault(); return; }
            e.preventDefault();

            accumulatedDelta += e.deltaY;
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(function() {
                if (Math.abs(accumulatedDelta) >= CONFIG.scrollThreshold) {
                    if (accumulatedDelta > 0 && current < slices.length - 1) goTo(current + 1);
                    else if (accumulatedDelta < 0 && current > 0) goTo(current - 1);
                }
                accumulatedDelta = 0;
            }, 80);
        }

        function handleKeydown(e) {
            if (transitioning) return;
            if (document.activeElement && ['INPUT', 'TEXTAREA'].indexOf(document.activeElement.tagName) !== -1) return;

            if (e.key === 'ArrowDown' || e.key === 'PageDown') {
                e.preventDefault();
                if (current < slices.length - 1) goTo(current + 1);
            } else if (e.key === 'ArrowUp' || e.key === 'PageUp') {
                e.preventDefault();
                if (current > 0) goTo(current - 1);
            }
        }

        function handleTouchStart(e) {
            touchStartY = e.touches[0].clientY;
            touchStartTime = Date.now();
        }

        function handleTouchMove(e) {
            if (transitioning) { e.preventDefault(); return; }

            var touchEndY = e.touches[0].clientY;
            var delta = touchStartY - touchEndY;
            var timeDelta = Date.now() - touchStartTime;

            if (Math.abs(delta) > 30 && timeDelta > 50) {
                e.preventDefault();
                // delta > 0 means the finger moved up, i.e. the same intent as
                // scrolling down: advance. This matched handleWheel's sign but
                // was applied inverted, so swiping up went backwards — and did
                // nothing at all on the first slice.
                if (delta > 0 && current < slices.length - 1) goTo(current + 1);
                else if (delta < 0 && current > 0) goTo(current - 1);
                touchStartY = touchEndY;
                touchStartTime = Date.now();
            }
        }

        window.addEventListener('wheel', handleWheel, { passive: false });
        window.addEventListener('keydown', handleKeydown);
        window.addEventListener('touchstart', handleTouchStart, { passive: true });
        window.addEventListener('touchmove', handleTouchMove, { passive: false });
    }

    function init() {
        document.querySelectorAll('[data-onepageatatime]').forEach(initOne);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
