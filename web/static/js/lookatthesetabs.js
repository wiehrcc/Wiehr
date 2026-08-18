
(function() {
    'use strict';

    var DOT_SRC = '/static/images/entities/dot.svg';

    function renderItem(index, isActive) {
        return isActive
            ? '<img src="' + DOT_SRC + '" class="flipthrough-dot" alt="Current section">'
            : '<span class="flipthrough-number">' + (index + 1) + '</span>';
    }


    function createNav(count, opts) {
        opts = opts || {};
        var current = opts.initial || 0;

        var nav = document.createElement('nav');
        nav.className = 'flipthrough';
        nav.setAttribute('aria-label', opts.ariaLabel || 'Sections');

        if (count > 1) {
            var html = '';
            for (var i = 0; i < count; i++) {
                if (i > 0) html += '<div class="flipthrough-line"></div>';
                html += '<div class="flipthrough-item' + (i === current ? ' active' : '') +
                    '" data-index="' + i + '">' + renderItem(i, i === current) + '</div>';
            }
            nav.innerHTML = html;
        }

        nav.addEventListener('click', function(e) {
            var item = e.target.closest('.flipthrough-item');
            if (!item) return;
            var index = parseInt(item.getAttribute('data-index'), 10);
            if (!isNaN(index) && opts.onSelect) opts.onSelect(index);
        });

        document.body.appendChild(nav);

        function setActive(index) {
            current = index;
            var items = nav.querySelectorAll('.flipthrough-item');
            items.forEach(function(item, i) {
                var isActive = i === index;
                item.classList.toggle('active', isActive);
                item.innerHTML = renderItem(i, isActive);
            });
        }

        function destroy() {
            if (nav.parentNode) nav.parentNode.removeChild(nav);
        }

        return { el: nav, setActive: setActive, destroy: destroy };
    }

    window.SectionFlipper = { createNav: createNav };
})();
