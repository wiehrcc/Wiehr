(function() {
    'use strict';

    var BARCODE_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()-_=+[]{}|;:<>?/~';

    var BACKDROP_PATH = '/static/images/backdrop/';

    var MENU_ITEMS = [
        { id: 'index', label: '•', icon: 'network.svg', backdrop: 'network.jpg', href: '/', active: true, isFirst: true },
        { id: 'archive', label: 'Archive', icon: 'archive.svg', backdrop: 'archive.jpg', href: '/archive', active: true },
        { id: 'globe', label: 'Globe', icon: 'globe.svg', backdrop: 'globe.jpg', href: '/globe', active: true },
        { id: 'atlas', label: 'Atlas', icon: 'atlas.svg', backdrop: 'atlas.jpg', href: '/atlas', active: true },
        { id: 'storage', label: 'Storage', icon: 'storage.svg', backdrop: 'storage.jpg', href: '/storage', active: true },
        { id: 'lab', label: 'Lab', icon: 'lab.svg', backdrop: 'lab.jpg', href: '/lab', active: true },
        { id: 'about', label: 'About', icon: 'whoareyou.svg', backdrop: 'whoareyou.jpg', href: '/about', active: true }
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

        
        
        var outlineFrame = null;
        function animateOutline() {
            var dx = endX - _x;
            var dy = endY - _y;
            if (Math.abs(dx) < 0.1 && Math.abs(dy) < 0.1) {
                outlineFrame = null;
                return;
            }
            _x += dx / delay;
            _y += dy / delay;
            cursorDotOutline.style.top = _y + 'px';
            cursorDotOutline.style.left = _x + 'px';
            outlineFrame = requestAnimationFrame(animateOutline);
        }
        function wakeOutline() {
            if (outlineFrame === null) outlineFrame = requestAnimationFrame(animateOutline);
        }
        document.addEventListener('mousemove', wakeOutline, { passive: true });
        wakeOutline();

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

            if (openOverlays === 1 && window.WiehrLoops) window.WiehrLoops.pauseAll();

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
            if (window.WiehrLoops) window.WiehrLoops.resumeAll();
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
        ['lightordarkness', 'lightordarkness-overlay'].forEach(function(id) {
            var btn = document.getElementById(id);
            if (!btn) return;
            btn.addEventListener('click', function() {
                triggerGlitch();
                if (window.WiehrTheme) window.WiehrTheme.toggle();
            });
        });
    }

    var ACCENT_KEY = 'wiehr-accent';

    function getAccent() {
        return localStorage.getItem(ACCENT_KEY) || 'none';
    }

    function applyAccent(accent) {
        if (accent === 'blood') {
            document.documentElement.setAttribute('data-wiehr-accent', 'blood');
        } else {
            document.documentElement.removeAttribute('data-wiehr-accent');
        }
        if (window._wiehrColorLoc && window.WebGLRenderingContext) {
            updateLogoAccentColor();
        }
    }

    function updateLogoAccentColor() {
        // defer to next frame so the logo render picks it up
    }

    function toggleAccent() {
        var current = getAccent();
        var next = current === 'blood' ? 'none' : 'blood';
        localStorage.setItem(ACCENT_KEY, next);
        applyAccent(next);
        return next;
    }

    applyAccent(getAccent());

    window.WiehrAccent = {
        get: getAccent,
        set: function(a) { localStorage.setItem(ACCENT_KEY, a); applyAccent(a); },
        toggle: toggleAccent
    };

    function initAccentToggle() {
        ['bloodordeath', 'bloodordeath-overlay'].forEach(function(id) {
            var btn = document.getElementById(id);
            if (!btn) return;
            btn.addEventListener('click', function() {
                triggerGlitch();
                toggleAccent();
            });
        });
    }

    function initMenu() {
        var menuBtn = document.getElementById('labyrinthopenseverything');
        var overlay = document.getElementById('whatareyouinterestedin');
        var itemsContainer = overlay ? overlay.querySelector('.routesforyou') : null;
        var menuOpen = false;
        var menuTransitioning = false;

        if (!menuBtn || !overlay || !itemsContainer) return;

        var currentPath = window.location.pathname;
        var html = '';
        var delayStep = 0;

        function isCurrentRoute(item) {
            var href = item.href;
            if (href === '/' && currentPath === '/') return true;
            if (href !== '/' && currentPath.indexOf(href) === 0) return true;
            if (item.id === 'about' && currentPath.indexOf('/rates') === 0) return true;
            return false;
        }

        function renderRoute(item, branch) {
            var isCurrent = isCurrentRoute(item);
            var disabled = item.active === false;
            var cls = 'singlerouteforyou';
            if (isCurrent) cls += ' singlerouteforyou-current';
            if (disabled) cls += ' singlerouteforyou-disabled';

            var out = '<div class="' + cls + '" style="transition-delay:' + (delayStep * 40) + 'ms"' +
                      (item.backdrop && !disabled ? ' data-routebackdrop="' + BACKDROP_PATH + item.backdrop + '"' : '') + '>';
            delayStep += 1;
            out += disabled
                ? '<span class="routelink routelink-disabled">'
                : '<a href="' + item.href + '" class="routelink">';
            out += disabled
                ? '<span class="routelabel classifiedlabel" data-len="' + item.label.length + '"></span>'
                : '<span class="routelabel">' + item.label + '</span>';
            out += '<img src="/static/images/entities/' + item.icon + '" alt="' + item.label +
                   '" class="routeicon' + (isCurrent ? ' routeicon-noise' : '') + '">';
            out += disabled ? '</span>' : '</a>';
            out += '</div>';
            return out;
        }

        MENU_ITEMS.forEach(function(item, i) {
            var isFirst = item.isFirst === true || i === 0;
            var isLast = i === MENU_ITEMS.length - 1;
            var branch = isLast ? '└──' : (isFirst ? '┌──' : '├──');
            html += renderRoute(item, branch);
        });
        itemsContainer.innerHTML = html;

        var preview = document.getElementById('wherewewouldgo');
        var previewShown = '';
        var preloaded = false;

        function preloadBackdrops() {
            if (preloaded) return;
            preloaded = true;
            overlay.querySelectorAll('[data-routebackdrop]').forEach(function(el) {
                (new Image()).src = el.getAttribute('data-routebackdrop');
            });
        }

        
        var previewTimer = null;
        var PREVIEW_SETTLE = 90;

        function showPreview(src) {
            if (!preview || previewShown === src) return;
            previewShown = src;
            preview.style.backgroundImage = "url('" + src + "')";
            preview.classList.add('showingitself');
        }

        function queuePreview(src) {
            if (!preview || previewShown === src) return;
            if (previewTimer) clearTimeout(previewTimer);
            previewTimer = setTimeout(function() {
                previewTimer = null;
                showPreview(src);
            }, PREVIEW_SETTLE);
        }

        function hidePreview() {
            if (!preview) return;
            if (previewTimer) { clearTimeout(previewTimer); previewTimer = null; }
            previewShown = '';
            preview.classList.remove('showingitself');
        }

        if (preview) {
            overlay.querySelectorAll('[data-routebackdrop]').forEach(function(row) {
                var src = row.getAttribute('data-routebackdrop');
                row.addEventListener('pointerenter', function() { queuePreview(src); });
                row.addEventListener('pointerleave', hidePreview);
            });

            itemsContainer.addEventListener('pointerleave', hidePreview);
        }

        function openMenu() {
            if (menuTransitioning) return;
            menuTransitioning = true;
            menuOpen = true;
            menuBtn.classList.add('menuisopen');
            document.body.classList.add('menuisopen');
            overlay.classList.add('awake');

            stopAllScrambles();
            overlay.querySelectorAll('.classifiedlabel').forEach(function(el) {
                startScramble(el, parseInt(el.getAttribute('data-len')) || 6);
            });

            var items = overlay.querySelectorAll('.singlerouteforyou');
            items.forEach(function(el, i) {
                setTimeout(function() { el.classList.add('shownitself'); }, i * 50);
            });

            var totalItems = items.length;

            if (window.WiehrLoops) window.WiehrLoops.pauseAll();

            setTimeout(function() { menuTransitioning = false; }, totalItems * 50 + 100);
        }

        function closeMenu() {
            if (menuTransitioning) return;
            menuTransitioning = true;
            menuOpen = false;
            menuBtn.classList.remove('menuisopen');
            document.body.classList.remove('menuisopen');
            stopAllScrambles();
            hidePreview();

            var items = overlay.querySelectorAll('.singlerouteforyou');
            items.forEach(function(el) { el.classList.remove('shownitself'); });

            setTimeout(function() {
                overlay.classList.remove('awake');
                if (window.WiehrLoops) window.WiehrLoops.resumeAll();
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
        'globe': { icon: 'globe.svg', href: '/globe', label: 'Globe' },
        'archive': { icon: 'archive.svg', href: '/archive', label: 'Archive' },
        'atlas': { icon: 'atlas.svg', href: '/atlas', label: 'Atlas' },
        'lab': { icon: 'lab.svg', href: '/lab', label: 'Lab' },
        'storage': { icon: 'storage.svg', href: '/storage', label: 'Storage' },
        'about': { icon: 'whoareyou.svg', href: '/about', label: 'About' },
        'rates': { icon: 'hire.svg', href: '/rates', label: 'Rates' },
        'privacy': { icon: 'legal.svg', href: '/privacy', label: 'Privacy' },
        'terms': { icon: 'legal.svg', href: '/terms', label: 'Terms' },
        'licensing': { icon: 'license.svg', href: '/licensing', label: 'Licensing' },
        's': { icon: 'shortener.svg', href: '/s', label: 'Shortener' }
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
            dotSpan.className = 'youareherelink youareherelink-dot';
            var dotImg = document.createElement('img');
            dotImg.className = 'youarehereicon youarehereicondot';
            dotImg.src = '/static/images/entities/dot.svg';
            dotImg.alt = 'Current page';
            dotSpan.appendChild(dotImg);

            nav.appendChild(breadcrumbLine());
            nav.appendChild(breadcrumbRow(dotSpan));
        }
    }

    function syncHeaderClearance() {
        var root = document.documentElement;
        var header = document.getElementById('acrossthetop');
        var logo = document.querySelector('.wilogoatleft');
        var crumbs = document.getElementById('youarehere');
        var footers = ['.copyrightmark:not(.copyrightmark--overlay)', '.flipthrough']
            .map(function(sel) { return document.querySelector(sel); })
            .filter(Boolean);

        function apply() {
            var cs = getComputedStyle(root);
            var rem = parseFloat(cs.fontSize) || 16;
            var inset = parseFloat(cs.getPropertyValue('--chrome-inset')) || 16;
            if (cs.getPropertyValue('--chrome-inset').indexOf('rem') !== -1) inset *= rem;
            var measure = parseFloat(cs.getPropertyValue('--page-width')) || 640;

            var vw = root.clientWidth;
            var paneWidth = Math.min(measure, vw - 2 * inset);
            var paneLeft = (vw - paneWidth) / 2;
            var paneRight = paneLeft + paneWidth;

            var barPaints = false;
            if (header) {
                var barBg = getComputedStyle(header).backgroundColor;
                barPaints = !!barBg && barBg !== 'transparent' &&
                            !/^rgba\(.*,\s*0\)$/.test(barBg);
            }

            var clear = 0;
            var candidates = barPaints ? [header] : [logo, crumbs];
            candidates.forEach(function(el) {
                if (!el) return;
                var b = el.getBoundingClientRect();
                if (!b.width) return;
                if (b.right > paneLeft && b.left < paneRight) {
                    clear = Math.max(clear, b.bottom);
                }
            });

            root.style.setProperty('--space-header', Math.round(clear + inset) + 'px');

            var vh = root.clientHeight;
            var floor = 0;
            footers.forEach(function(el) {
                if (!el) return;
                var b = el.getBoundingClientRect();
                if (!b.width) return;
                if (b.right > paneLeft && b.left < paneRight) {
                    floor = Math.max(floor, vh - b.top);
                }
            });
            root.style.setProperty('--space-bottom', Math.round(floor + inset) + 'px');

            var marks = 0;
            ['.copyrightmark:not(.copyrightmark--overlay)'].forEach(function(sel) {
                var el = document.querySelector(sel);
                if (el) marks = Math.max(marks, el.getBoundingClientRect().height);
            });
            root.style.setProperty('--footer-marks', Math.round(marks) + 'px');
        }

        apply();
        window.addEventListener('resize', apply);
        if (window.ResizeObserver) {
            [header, logo, crumbs].concat(footers).forEach(function(el) {
                if (el) new ResizeObserver(apply).observe(el);
            });
        }
        if (document.fonts && document.fonts.ready) document.fonts.ready.then(apply);
    }

    window.triggerGlitch = triggerGlitch;

    document.addEventListener('DOMContentLoaded', function() {
        initCursor();
        initThemeToggle();
        initAccentToggle();
        initMenu();
        initBreadcrumbs();
        syncHeaderClearance();
    });
})();
