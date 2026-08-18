(function() {
    'use strict';

    var BARCODE_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()-_=+[]{}|;:<>?/~';

    var MENU_ITEMS = [
        { id: 'index', label: '•', icon: 'network.svg', href: '/', active: true, isFirst: true },
        { id: 'archive', label: 'ARCHIVE', icon: 'archive.svg', href: '/archive', active: true },
        { id: 'globe', label: 'GLOBE', icon: 'globe.svg', href: '/globe', active: true },
        { id: 'atlas', label: 'ATLAS', icon: 'atlas.svg', href: '/atlas', active: true },
        { id: 'storage', label: 'STORAGE', icon: 'storage.svg', href: '/storage', active: true },
        { id: 'lab', label: 'LAB', icon: 'lab.svg', href: '/lab', active: true },
        { id: 'whoareyou', label: 'WHO ARE YOU?', icon: 'whoareyou.svg', href: '/whoareyou', active: true }
    ];


    function initCursor() {
        if (window.innerWidth <= 640 || ('ontouchstart' in window)) return;

        var cursorDot = document.createElement('div');
        var cursorDotOutline = document.createElement('div');
        cursorDot.className = 'cursor-dot';
        cursorDotOutline.className = 'cursor-dot-outline';
        document.body.appendChild(cursorDotOutline);
        document.body.appendChild(cursorDot);

        var delay = 8;
        var _x = 0;
        var _y = 0;
        var endX = 0;
        var endY = 0;
        var hasMoved = false;

        cursorDot.style.opacity = 0;
        cursorDotOutline.style.opacity = 0;

        document.querySelectorAll('a, button, [role="button"], .clickable').forEach(function(el) {
            el.addEventListener('mouseover', function() {
                cursorDot.classList.add('hover');
                cursorDotOutline.classList.add('hover');
            });
            el.addEventListener('mouseout', function() {
                cursorDot.classList.remove('hover');
                cursorDotOutline.classList.remove('hover');
            });
        });

        document.addEventListener('mousemove', function(e) {
            endX = e.clientX;
            endY = e.clientY;
            cursorDot.style.top = endY + 'px';
            cursorDot.style.left = endX + 'px';
            if (!hasMoved) {
                hasMoved = true;
                _x = endX;
                _y = endY;
                cursorDotOutline.style.top = endY + 'px';
                cursorDotOutline.style.left = endX + 'px';
                cursorDot.style.opacity = 1;
                cursorDotOutline.style.opacity = 1;
            }
        });

        document.addEventListener('mouseenter', function() {
            if (hasMoved) {
                cursorDot.style.opacity = 1;
                cursorDotOutline.style.opacity = 1;
            }
        });

        document.addEventListener('mouseleave', function() {
            cursorDot.style.opacity = 0;
            cursorDotOutline.style.opacity = 0;
        });

        function animateOutline() {
            _x += (endX - _x) / delay;
            _y += (endY - _y) / delay;
            cursorDotOutline.style.top = _y + 'px';
            cursorDotOutline.style.left = _x + 'px';
            requestAnimationFrame(animateOutline);
        }
        animateOutline();


        window.WiehrCursor = {
            hide: function() {
                cursorDot.style.display = 'none';
                cursorDotOutline.style.display = 'none';
            },
            show: function() {
                cursorDot.style.display = '';
                cursorDotOutline.style.display = '';
            }
        };
    }


    window.WiehrCursor = window.WiehrCursor || { hide: function() {}, show: function() {} };


    var openOverlays = 0;

    window.WiehrOverlay = {
        open: function(options) {
            options = options || {};
            openOverlays++;
            document.body.classList.add('nothingelsematters');
            document.body.style.overflow = 'hidden';


            if (options.nativeCursor) {
                document.body.classList.add('cursorisnotmine');
                window.WiehrCursor.hide();
            }
        },
        close: function() {
            openOverlays = Math.max(0, openOverlays - 1);
            if (openOverlays > 0) return;
            document.body.classList.remove('nothingelsematters');
            document.body.classList.remove('cursorisnotmine');
            document.body.style.overflow = '';
            window.WiehrCursor.show();
        }
    };

    function generateBarcode(len) {
        var s = '';
        for (var j = 0; j < len; j++) {
            s += BARCODE_CHARS[Math.floor(Math.random() * BARCODE_CHARS.length)];
        }
        return s;
    }

    var scrambleIntervals = [];

    function startScramble(el, len) {
        el.textContent = generateBarcode(len);
        var id = setInterval(function() {
            el.textContent = generateBarcode(len);
        }, 1000);
        scrambleIntervals.push(id);
    }

    function stopAllScrambles() {
        scrambleIntervals.forEach(function(id) { clearInterval(id); });
        scrambleIntervals = [];
    }

    function triggerGlitch() {
        document.body.classList.remove('themeglitch');
        void document.body.offsetWidth;
        document.body.classList.add('themeglitch');
        setTimeout(function() { document.body.classList.remove('themeglitch'); }, 400);
    }

    function initThemeToggle() {
        var btn = document.getElementById('lightordarkness');
        if (!btn) return;
        btn.addEventListener('click', function() {
            triggerGlitch();
            if (window.WiehrTheme) window.WiehrTheme.toggle();
        });
    }

    function initMenu() {
        var menuBtn = document.getElementById('labyrinthopenseverything');
        var overlay = document.getElementById('whatareyouinterestedin');
        var menuBottom = document.getElementById('bottomofeverything');
        var versionMark = document.getElementById('versionmark');
        var copyrightMark = document.getElementById('copyrightmark');
        var itemsContainer = overlay ? overlay.querySelector('.routesforyou') : null;
        var menuOpen = false;
        var menuTransitioning = false;

        if (!menuBtn || !overlay || !itemsContainer) return;

        var currentPath = window.location.pathname;
        var html = '';
        MENU_ITEMS.forEach(function(item, i) {
            var isFirst = item.isFirst === true || i === 0;
            var isLast = i === MENU_ITEMS.length - 1;
            var branch = isLast ? '└──' : (isFirst ? '┌──' : '├──');
            var isCurrent = (item.href === '/' && currentPath === '/') ||
                           (item.href !== '/' && currentPath.indexOf(item.href) === 0);
            var disabled = item.active === false;
            var cls = 'singlerouteforyou';
            if (isCurrent) cls += ' singlerouteforyou-current';
            if (disabled) cls += ' singlerouteforyou-disabled';
            html += '<div class="' + cls + '" style="transition-delay:' + (i * 40) + 'ms">';
            html += '<span class="treebranch">' + branch + '</span>';
            if (disabled) {
                html += '<span class="routelink routelink-disabled">';
            } else {
                html += '<a href="' + item.href + '" class="routelink">';
            }
            if (isCurrent) {
                html += '<img src="/static/images/entities/' + item.icon + '" alt="' + item.label + '" class="routeicon routeicon-noise">';
            } else {
                html += '<img src="/static/images/entities/' + item.icon + '" alt="' + item.label + '" class="routeicon">';
            }
            if (disabled) {
                html += '<span class="routelabel classifiedlabel" data-len="' + item.label.length + '"></span>';
            } else {
                html += '<span class="routelabel">' + item.label + '</span>';
            }
            html += disabled ? '</span>' : '</a>';
            if (!disabled) {
                html += '<span class="routepath">' + item.href + '</span>';
            }
            html += '</div>';
        });
        itemsContainer.innerHTML = html;


        var themeBtn = document.getElementById('lightordarkness');

        function getFooterLinks() {
            return menuBottom ? menuBottom.querySelectorAll('.lastresortlink, .lastresortsep') : [];
        }

        function openMenu() {
            if (menuTransitioning) return;
            menuTransitioning = true;
            menuOpen = true;
            menuBtn.classList.add('menuisopen');
            document.body.classList.add('menuisopen');
            overlay.classList.add('awake');
            triggerGlitch();

            if (themeBtn) themeBtn.style.display = 'flex';
            if (menuBottom) menuBottom.classList.add('shownitself');
            if (menuBottom) void menuBottom.offsetHeight;
            if (versionMark) versionMark.classList.add('hidden');
            if (copyrightMark) copyrightMark.classList.add('hidden');

            stopAllScrambles();
            overlay.querySelectorAll('.classifiedlabel').forEach(function(el) {
                startScramble(el, parseInt(el.getAttribute('data-len')) || 6);
            });

            var items = overlay.querySelectorAll('.singlerouteforyou');
            items.forEach(function(el, i) {
                setTimeout(function() { el.classList.add('shownitself'); }, i * 50);
            });

            var totalItems = items.length;

            var footerLinks = getFooterLinks();
            footerLinks.forEach(function(el) { el.classList.add('shownitself'); });
            if (themeBtn) themeBtn.classList.add('shownitself');
            if (window.pauseWebGL) window.pauseWebGL();

            setTimeout(function() { menuTransitioning = false; }, totalItems * 50 + 100);
        }

        function closeMenu() {
            if (menuTransitioning) return;
            menuTransitioning = true;
            menuOpen = false;
            menuBtn.classList.remove('menuisopen');
            document.body.classList.remove('menuisopen');
            stopAllScrambles();

            var items = overlay.querySelectorAll('.singlerouteforyou');
            items.forEach(function(el) { el.classList.remove('shownitself'); });
            var footerLinks = getFooterLinks();
            footerLinks.forEach(function(el) { el.classList.remove('shownitself'); });
            if (themeBtn) themeBtn.classList.remove('shownitself');

            setTimeout(function() {
                overlay.classList.remove('awake');
                if (menuBottom) menuBottom.classList.remove('shownitself');
                if (themeBtn) themeBtn.style.display = 'none';
                if (versionMark) versionMark.classList.remove('hidden');
                if (copyrightMark) copyrightMark.classList.remove('hidden');
                if (window.resumeWebGL) window.resumeWebGL();
                menuTransitioning = false;
            }, 250);
        }

        menuBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            if (menuOpen) closeMenu(); else openMenu();
        });

        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && menuOpen) closeMenu();
        });

        overlay.addEventListener('click', function(e) {
            if (e.target === overlay || e.target.classList.contains('pickyourdestination')) {
                closeMenu();
            }
        });

        window.WiehrMenu = { open: openMenu, close: closeMenu, isOpen: function() { return menuOpen; } };
    }

    var BREADCRUMB_ENTITIES = {
        'globe': { icon: 'globe.svg', href: '/globe', label: 'GLOBE' },
        'archive': { icon: 'archive.svg', href: '/archive', label: 'ARCHIVE' },
        'atlas': { icon: 'atlas.svg', href: '/atlas', label: 'ATLAS' },
        'lab': { icon: 'lab.svg', href: '/lab', label: 'LAB' },
        'storage': { icon: 'storage.svg', href: '/storage', label: 'STORAGE' },
        'composer': { icon: 'hire.svg', href: '/composer', label: 'COMPOSER' },
        'engineer': { icon: 'hire.svg', href: '/engineer', label: 'ENGINEER' },
        'whoareyou': { icon: 'whoareyou.svg', href: '/whoareyou', label: 'WHO ARE YOU?' },
        'support': { icon: 'legal.svg', href: '/support', label: 'SUPPORT' },
        'privacy': { icon: 'legal.svg', href: '/privacy', label: 'PRIVACY' },
        'terms': { icon: 'legal.svg', href: '/terms', label: 'TERMS' },
        'licensing': { icon: 'legal.svg', href: '/licensing', label: 'LICENSING' },
        's': { icon: 'shortener.svg', href: '/s', label: 'SHORTENER' }
    };


    function breadcrumbRow(iconEl) {
        var row = document.createElement('div');
        row.className = 'youarehereitem';
        row.appendChild(iconEl);
        return row;
    }

    function breadcrumbLine() {
        var line = document.createElement('div');
        line.className = 'youarehereline';
        return line;
    }


    function objectLabel(parts) {
        var declared = (document.body.getAttribute('data-breadcrumb-label') || '').trim();
        if (declared) return declared.toUpperCase();
        return decodeURIComponent(parts[parts.length - 1]).replace(/[-_]+/g, ' ').toUpperCase();
    }

    function initBreadcrumbs() {
        var nav = document.getElementById('youarehere');
        if (!nav) return;

        var path = window.location.pathname.replace(/\/+$/, '') || '/';
        var parts = path.split('/').filter(Boolean);
        if (parts.length === 0) return;

        var entity = parts[0];
        var cfg = BREADCRUMB_ENTITIES[entity];
        if (!cfg) return;

        var entityLink = document.createElement('a');
        entityLink.className = 'youareherelink noiseonhover';
        entityLink.href = cfg.href;
        entityLink.setAttribute('aria-label', cfg.label);
        var entityImg = document.createElement('img');
        entityImg.className = 'youarehereicon';
        entityImg.src = '/static/images/entities/' + cfg.icon;
        entityImg.alt = cfg.label;
        entityLink.appendChild(entityImg);

        nav.appendChild(breadcrumbLine());
        nav.appendChild(breadcrumbRow(entityLink));

        if (parts.length >= 2) {
            var dotSpan = document.createElement('span');
            dotSpan.className = 'youareherelink';
            var dotImg = document.createElement('img');
            dotImg.className = 'youarehereicon youarehereicondot';
            dotImg.src = '/static/images/entities/dot.svg';
            dotImg.alt = 'Current page';
            dotSpan.appendChild(dotImg);

            nav.appendChild(breadcrumbLine());
            nav.appendChild(breadcrumbRow(dotSpan));
        }
    }

    window.triggerGlitch = triggerGlitch;

    document.addEventListener('DOMContentLoaded', function() {
        initCursor();
        initThemeToggle();
        initMenu();
        initBreadcrumbs();
    });
})();
