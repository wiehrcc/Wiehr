/* One answer to "how much can this device take?", decided once.

   Three tiers. `high` is the site as designed — nothing is held back. `mid`
   and `low` keep every visual: the glass, the backdrops, the colours, the
   layout. What they give up is *smoothness, density and background work* —
   fewer particles, fewer frames per second, fewer things running while you are
   not looking at them.

   This used to be three separate guesses. waitforitall.js, floatingdust.js and
   webgl-globe.js each re-derived cores/memory/user-agent on their own and
   disagreed about the answer, and the one shared flag was published far too
   late for CSS to see it. Now it is one decision, stamped on <html> before
   first paint, so a stylesheet can react without a flash.

   The user-agent rule mattered most. Every one of the old checks did
   `isMobile -> low`, which put an iPhone 12 in the same bucket as a budget
   Android from 2016. Mobile now *caps* the tier at `mid` rather than forcing
   `low`, and a missing navigator.deviceMemory is not held against iOS, which
   simply does not implement it. */

(function () {
    'use strict';

    var root = document.documentElement;

    function detect() {
        var nav = navigator;

        /* prefers-reduced-motion is NOT a performance signal.

           It used to return 'low' here, which is a category error: the setting
           is about vestibular safety, not about how fast the machine is. The
           effect was that anyone with "reduce animations" ticked in Windows or
           macOS — on any hardware at all — got the 20fps cap and the bottom
           tier, and the site felt like it was lagging on a 12-core desktop.
           Reduced motion is honoured in CSS, where it belongs: animations off,
           transitions short. The frame budget is left to the hardware. */

        var conn = nav.connection || nav.mozConnection || nav.webkitConnection;
        if (conn && (conn.saveData === true || /(^|-)2g$/.test(conn.effectiveType || ''))) {
            return 'low';
        }

        var ua = nav.userAgent || '';
        var isIOS = /iPad|iPhone|iPod/.test(ua) ||
                    (nav.platform === 'MacIntel' && nav.maxTouchPoints > 1);
        var isMobile = isIOS || /Android|webOS|BlackBerry|IEMobile|Opera Mini/i.test(ua);

        var cores = nav.hardwareConcurrency || 0;

        // Safari does not implement deviceMemory at all. Treating "absent" as
        // "small" is what pushed every iPhone into the bottom tier.
        var mem = nav.deviceMemory || 0;
        var memKnown = mem > 0;

        var tier;
        if (cores >= 8 && (!memKnown || mem >= 8)) {
            tier = 'high';
        } else if (cores >= 4 && (!memKnown || mem >= 4)) {
            tier = 'mid';
        } else if (cores === 0 && !memKnown) {
            // Told nothing at all: assume the middle rather than the floor.
            tier = 'mid';
        } else {
            tier = 'low';
        }

        // A phone is never `high`, however many cores it reports — the ceiling
        // there is thermal and battery, not arithmetic.
        if (isMobile && tier === 'high') tier = 'mid';

        return tier;
    }

    /* An escape hatch, because the guess above is a guess. `?tier=high` pins a
       tier for one visit and remembers it; `?tier=auto` forgets it again. */
    function override() {
        var pinned = null;
        try {
            var q = /[?&]tier=(high|mid|low|auto)(?:&|$)/.exec(location.search);
            if (q) {
                if (q[1] === 'auto') localStorage.removeItem('wiehr-tier');
                else localStorage.setItem('wiehr-tier', q[1]);
            }
            pinned = localStorage.getItem('wiehr-tier');
        } catch (e) { /* private mode */ }
        return (pinned === 'high' || pinned === 'mid' || pinned === 'low') ? pinned : null;
    }

    var name = override() || detect();
    var ORDER = { low: 0, mid: 1, high: 2 };
    /* Every tier is capped, `high` included — a 144Hz monitor should not mean
       144 physics steps a second just because it can. On a 60Hz display the
       high cap is a no-op; above 60Hz it is the point.

       The caps divide into 60. That is not cosmetic: 24fps on a 60Hz display
       is unreachable, and asking for it gets you an alternating 2-3 frame gap
       (judder that reads worse than a steady 20) or, with a strict gate, a
       silent collapse to 20 anyway. 60 / 30 / 20 are the three rates a 60Hz
       display can actually hold.

       The tolerance is what makes the gate honest. Without it: two 60Hz frames
       are 2 x (1000/60) = 33.33333333333333ms, a 30fps interval is
       1000/30 = 33.333333333333336ms — fractionally larger — so the second
       frame is judged "too early", the cap falls through to every third frame,
       and a 30fps setting quietly delivers 20. */
    var FPS = { low: 20, mid: 30, high: 60 };
    var FRAME_TOLERANCE = 4;

    root.setAttribute('data-tier', name);

    var Tier = {
        name: name,

        is: function (n) { return name === n; },
        atLeast: function (n) { return ORDER[name] >= ORDER[n]; },

        /* Pick a number per tier: Tier.pick(140, 70, 30). */
        pick: function (high, mid, low) {
            return name === 'high' ? high : (name === 'mid' ? mid : low);
        },

        fps: FPS[name],

        /* A frame loop that respects the tier and stops when the tab is hidden.
           Every animated module used to hand-roll its own rAF plus its own
           visibilitychange handling; this is that, once.

           `cb` receives the timestamp. Returns a stop() function. */
        frame: function (cb) {
            var id = null;
            var stopped = false;
            var last = 0;
            var interval = FPS[name] ? 1000 / FPS[name] - FRAME_TOLERANCE : 0;

            function tick(now) {
                if (stopped) return;
                id = requestAnimationFrame(tick);
                if (interval && now - last < interval) return;
                last = now;
                cb(now);
            }

            function start() {
                if (stopped || id !== null) return;
                last = 0;
                id = requestAnimationFrame(tick);
            }

            function pause() {
                if (id !== null) { cancelAnimationFrame(id); id = null; }
            }

            function onVisibility() {
                if (document.hidden) pause(); else start();
            }

            document.addEventListener('visibilitychange', onVisibility);
            if (!document.hidden) start();

            return function stop() {
                stopped = true;
                pause();
                document.removeEventListener('visibilitychange', onVisibility);
            };
        }
    };

    window.WiehrTier = Tier;

    // webgl-globe.js has read this since before the tiers existed.
    window.WIEHR_PERFORMANCE = name === 'mid' ? 'medium' : name;
})();
