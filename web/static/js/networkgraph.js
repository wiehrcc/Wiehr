(function() {
    'use strict';


    var locationInput = document.getElementById('wherearetheyfrominput');
    var locationResults = document.getElementById('wherearetheyfromresults');
    var countryField = document.getElementById('wherearetheyfromname');
    var countryCodeField = document.getElementById('wherearetheyfromcode');
    var debounceTimer = null;

    function searchCountries(query) {
        if (!query || query.length < 2) return [];
        if (typeof COUNTRIES === 'undefined') return [];
        var q = query.toLowerCase();
        var matches = [];
        for (var i = 0; i < COUNTRIES.length; i++) {
            var c = COUNTRIES[i];
            var name = c[0].toLowerCase();
            var code = c[1].toLowerCase();
            if (name.indexOf(q) === 0 || code === q) {
                matches.push({ country: c[0], code: c[1], lat: c[2], lng: c[3] });
                if (matches.length >= 8) break;
            }
        }
        return matches;
    }

    function showResults(matches) {
        if (!locationResults) return;
        if (matches.length === 0) {
            locationResults.classList.remove('open');
            locationResults.innerHTML = '';
            return;
        }
        var html = '';
        for (var i = 0; i < matches.length; i++) {
            html += '<div class="oneofthemcountries" data-country="' + matches[i].country +
                '" data-code="' + matches[i].code + '">' +
                matches[i].country + '</div>';
        }
        locationResults.innerHTML = html;
        locationResults.classList.add('open');

        locationResults.querySelectorAll('.oneofthemcountries').forEach(function(el) {
            el.addEventListener('click', function() {
                var country = this.getAttribute('data-country');
                var code = this.getAttribute('data-code');
                locationInput.value = country;
                countryField.value = country;
                countryCodeField.value = code;
                locationResults.classList.remove('open');
                locationResults.innerHTML = '';
            });
        });
    }

    if (locationInput) {
        locationInput.addEventListener('input', function() {
            clearTimeout(debounceTimer);
            var val = this.value;
            debounceTimer = setTimeout(function() {
                var matches = searchCountries(val);
                showResults(matches);
            }, 100);
        });

        locationInput.addEventListener('blur', function() {
            setTimeout(function() {
                if (locationResults) locationResults.classList.remove('open');
            }, 200);
        });

        locationInput.addEventListener('focus', function() {
            if (this.value.length >= 2) {
                showResults(searchCountries(this.value));
            }
        });
    }


    var modal = document.getElementById('pleasedontleave');
    var addBtn = document.getElementById('becomevisible');
    var form = document.getElementById('formalitieskillus');
    var status = document.getElementById('didithappen');

    var menuBtnIcon = document.querySelector('.labyrinthopenseverything .labyrinthicon');
    var menuBtnOrigSrc = menuBtnIcon ? menuBtnIcon.getAttribute('src') : null;
    var youAreHereNav = document.querySelector('.youarehere');
    var closeSvgSrc = '/static/images/entities/notok.svg';

    function openModal() {
        if (!modal) return;
        window.logoInteractionBlocked = true;
        modal.style.display = 'flex';
        setTimeout(function() { modal.classList.add('awake'); }, 10);
        if (menuBtnIcon && closeSvgSrc) {
            menuBtnIcon.setAttribute('src', closeSvgSrc);
        }
        if (youAreHereNav) youAreHereNav.classList.add('no-glass');
    }

    function closeModal() {
        if (!modal) return;
        window.logoInteractionBlocked = false;
        modal.classList.remove('awake');
        setTimeout(function() { modal.style.display = 'none'; }, 300);
        if (menuBtnIcon && menuBtnOrigSrc) {
            menuBtnIcon.setAttribute('src', menuBtnOrigSrc);
        }
        if (youAreHereNav) youAreHereNav.classList.remove('no-glass');
    }

    if (addBtn) addBtn.addEventListener('click', openModal);
    if (modal) modal.addEventListener('click', function(e) { if (e.target === modal) closeModal(); });
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && modal && modal.style.display !== 'none') closeModal();
    });


    var menuBtn = document.getElementById('labyrinthopenseverything');
    if (menuBtn) {
        menuBtn.addEventListener('click', function(e) {
            if (modal && modal.style.display !== 'none' && modal.classList.contains('awake')) {
                e.stopPropagation();
                e.preventDefault();
                closeModal();
            }
        }, true);
    }

    function getCookie(name) {
        var v = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
        return v ? v.pop() : '';
    }

    function resolveTypedCountry() {
        if (!locationInput) return null;
        var typed = (locationInput.value || '').trim().toLowerCase();
        if (!typed || typeof COUNTRIES === 'undefined') return null;
        for (var i = 0; i < COUNTRIES.length; i++) {
            if (COUNTRIES[i][0].toLowerCase() === typed || COUNTRIES[i][1].toLowerCase() === typed) {
                return { country: COUNTRIES[i][0], code: COUNTRIES[i][1] };
            }
        }
        var hits = [];
        for (var j = 0; j < COUNTRIES.length; j++) {
            if (COUNTRIES[j][0].toLowerCase().indexOf(typed) === 0) hits.push(COUNTRIES[j]);
            if (hits.length > 1) return null;
        }
        return hits.length === 1 ? { country: hits[0][0], code: hits[0][1] } : null;
    }

    if (locationInput) {
        locationInput.addEventListener('blur', function() {
            var hit = resolveTypedCountry();
            if (!hit) return;
            locationInput.value = hit.country;
            if (countryField) countryField.value = hit.country;
            if (countryCodeField) countryCodeField.value = hit.code;
        });
    }

    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            var email = form.querySelector('[name="email"]').value;
            var country = countryField ? countryField.value : '';
            var countryCode = countryCodeField ? countryCodeField.value : '';

            if (!country || !countryCode) {
                var hit = resolveTypedCountry();
                if (hit) { country = hit.country; countryCode = hit.code; }
            }

            if (status) status.textContent = 'Subscribing...';

            fetch('/api/subscribe', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
                body: JSON.stringify({ email: email, country: country, country_code: countryCode })
            }).then(function(r) { return r.json(); }).then(function(data) {
                if (status) status.textContent = data.message || 'You are in the network now.';
                form.reset();
                if (countryField) countryField.value = '';
                if (countryCodeField) countryCodeField.value = '';
                var counter = document.getElementById('wecountsoulsnumber');
                if (counter && typeof data.visible_listeners === 'number') {
                    counter.textContent = data.visible_listeners;
                }

                if (window._reloadNetwork) window._reloadNetwork();
            }).catch(function() {
                if (status) status.textContent = 'You are in the network now.';
                form.reset();
            });
        });
    }


    var networkCanvas = document.getElementById('linesbetweenus');
    if (!networkCanvas) return;

    var nctx = networkCanvas.getContext('2d');
    if (!nctx) return;

    var networkAnimId = null;

    function resizeNetwork() {
        networkCanvas.width = window.innerWidth;
        networkCanvas.height = window.innerHeight;
        networkCanvas.style.width = '100%';
        networkCanvas.style.height = '100%';
    }

    resizeNetwork();
    window.addEventListener('resize', resizeNetwork);

    function isDark() {
        return document.documentElement.getAttribute('data-wiehr-theme') === 'dark';
    }

    function fgColor(alpha) {
        return isDark()
            ? 'rgba(244, 244, 244, ' + alpha + ')'
            : 'rgba(0, 0, 0, ' + alpha + ')';
    }

    function drawLabel(x1, y1, x2, y2, label, alpha) {
        var mx = (x1 + x2) / 2;
        var my = (y1 + y2) / 2;
        var angle = Math.atan2(y2 - y1, x2 - x1);
        nctx.save();
        nctx.translate(mx, my);
        var drawAngle = angle;
        if (drawAngle > Math.PI / 2) drawAngle -= Math.PI;
        if (drawAngle < -Math.PI / 2) drawAngle += Math.PI;
        nctx.rotate(drawAngle);
        nctx.font = 'bold 9px monospace';
        nctx.textAlign = 'center';
        nctx.textBaseline = 'middle';
        nctx.fillStyle = fgColor(alpha);
        nctx.fillText(label, 0, -8);
        nctx.restore();
    }


    var ripples = [];
    var nextRippleAt = 0;

    function spawnRipple(now) {
        var w = networkCanvas.width;
        var h = networkCanvas.height;
        var cx = w / 2;
        var cy = h / 2;
        var roll = Math.random();
        var ox = cx;
        var oy = cy;

        var projected = window._networkProjected || [];
        if (roll > 0.75 && projected.length) {
            var node = projected[(Math.random() * projected.length) | 0];
            ox = cx + node.x * cx;
            oy = cy - node.y * cy;
        } else if (roll > 0.6) {
            ox = Math.random() * w;
            oy = Math.random() * h;
        }

        ripples.push({
            x: ox,
            y: oy,
            born: now,

            life: 2600 + Math.random() * 3400,
            reach: Math.max(w, h) * (0.35 + Math.random() * 0.65),
            rings: 1 + ((Math.random() * 3) | 0),
            strength: 0.06 + Math.random() * 0.1
        });

        if (ripples.length > 12) ripples.shift();
    }

    function drawRipples(now) {
        for (var i = ripples.length - 1; i >= 0; i--) {
            var r = ripples[i];
            var age = (now - r.born) / r.life;
            if (age >= 1) {
                ripples.splice(i, 1);
                continue;
            }


            var spread = 1 - Math.pow(1 - age, 2.4);
            var fade = Math.pow(1 - age, 1.8);

            for (var k = 0; k < r.rings; k++) {
                var radius = (spread - k * 0.08) * r.reach;
                if (radius <= 0) continue;
                nctx.beginPath();
                nctx.arc(r.x, r.y, radius, 0, Math.PI * 2);
                nctx.strokeStyle = fgColor(r.strength * fade / (k + 1));
                nctx.lineWidth = 0.6;
                nctx.stroke();
            }
        }
    }

    /* Frame budget from the shared tier — see js/howfastareyou.js. */
    var NET_FRAME_MS = (window.WiehrTier && window.WiehrTier.fps)
        ? 1000 / window.WiehrTier.fps - 4 : 0;   // -4: see frame() in howfastareyou.js
    var netLastFrameAt = 0;

    function drawFrame(now) {
        now = now || 0;

        if (NET_FRAME_MS && now - netLastFrameAt < NET_FRAME_MS) {
            networkAnimId = requestAnimationFrame(drawFrame);
            return;
        }
        netLastFrameAt = now;

        var w = networkCanvas.width;
        var h = networkCanvas.height;
        nctx.clearRect(0, 0, w, h);

        if (now >= nextRippleAt) {
            spawnRipple(now);
            nextRippleAt = now + 900 + Math.random() * 2600;
        }
        drawRipples(now);

        var projected = window._networkProjected;
        if (!projected || projected.length === 0) {
            networkAnimId = requestAnimationFrame(drawFrame);
            return;
        }

        var cx = w / 2;
        var cy = h / 2;


        function toScreenX(nx) { return cx + nx * cx; }
        function toScreenY(ny) { return cy - ny * cy; }


        for (var i = 0; i < projected.length; i++) {
            var node = projected[i];
            if (node.isChild) continue;
            var sx = toScreenX(node.x);
            var sy = toScreenY(node.y);
            nctx.beginPath();
            nctx.moveTo(cx, cy);
            nctx.lineTo(sx, sy);
            nctx.strokeStyle = fgColor(0.12);
            nctx.lineWidth = 0.5;
            nctx.stroke();
            drawLabel(cx, cy, sx, sy, node.country, 0.28);
        }


        for (var j = 0; j < projected.length; j++) {
            var child = projected[j];
            if (!child.isChild || child.parentIdx < 0) continue;
            var parent = projected[child.parentIdx];
            if (!parent) continue;
            nctx.beginPath();
            nctx.moveTo(toScreenX(parent.x), toScreenY(parent.y));
            nctx.lineTo(toScreenX(child.x), toScreenY(child.y));
            nctx.strokeStyle = fgColor(0.09);
            nctx.lineWidth = 0.5;
            nctx.stroke();
        }

        networkAnimId = requestAnimationFrame(drawFrame);
    }


    var origPause = window.pauseWebGL;
    var origResume = window.resumeWebGL;

    window.pauseWebGL = function() {
        if (origPause) origPause();
        if (networkAnimId) {
            cancelAnimationFrame(networkAnimId);
            networkAnimId = null;
        }
    };

    window.resumeWebGL = function() {
        if (origResume) origResume();
        if (!networkAnimId) drawFrame();
    };

    drawFrame();
})();
