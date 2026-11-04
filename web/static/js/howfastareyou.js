

(function () {
    'use strict';

    var root = document.documentElement;

    function detect() {
        var nav = navigator;

        

        var conn = nav.connection || nav.mozConnection || nav.webkitConnection;
        if (conn && (conn.saveData === true || /(^|-)2g$/.test(conn.effectiveType || ''))) {
            return 'low';
        }

        var ua = nav.userAgent || '';
        var isIOS = /iPad|iPhone|iPod/.test(ua) ||
                    (nav.platform === 'MacIntel' && nav.maxTouchPoints > 1);
        var isMobile = isIOS || /Android|webOS|BlackBerry|IEMobile|Opera Mini/i.test(ua);

        var cores = nav.hardwareConcurrency || 0;

        
        
        var mem = nav.deviceMemory || 0;
        var memKnown = mem > 0;

        var tier;
        if (cores >= 8 && (!memKnown || mem >= 8)) {
            tier = 'high';
        } else if (cores >= 4 && (!memKnown || mem >= 4)) {
            tier = 'mid';
        } else if (cores === 0 && !memKnown) {
            
            tier = 'mid';
        } else {
            tier = 'low';
        }

        
        
        if (isMobile && tier === 'high') tier = 'mid';

        return tier;
    }

    
    function override() {
        var pinned = null;
        try {
            var q = /[?&]tier=(high|mid|low|auto)(?:&|$)/.exec(location.search);
            if (q) {
                if (q[1] === 'auto') localStorage.removeItem('wiehr-tier');
                else localStorage.setItem('wiehr-tier', q[1]);
            }
            pinned = localStorage.getItem('wiehr-tier');
        } catch (e) {  }
        return (pinned === 'high' || pinned === 'mid' || pinned === 'low') ? pinned : null;
    }

    var name = override() || detect();
    var ORDER = { low: 0, mid: 1, high: 2 };
    
    var FPS = { low: 20, mid: 30, high: 60 };
    var FRAME_TOLERANCE = 4;

    root.setAttribute('data-tier', name);

    var Tier = {
        name: name,

        is: function (n) { return name === n; },
        atLeast: function (n) { return ORDER[name] >= ORDER[n]; },

        
        pick: function (high, mid, low) {
            return name === 'high' ? high : (name === 'mid' ? mid : low);
        },

        fps: FPS[name],

        
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

    
    var loops = [];
    window.WiehrLoops = {
        add: function (pause, resume) {
            loops.push({ pause: pause, resume: resume, paused: false });
        },
        pauseAll: function () {
            loops.forEach(function (l) {
                if (!l.paused) { l.paused = true; try { l.pause(); } catch (e) {} }
            });
        },
        resumeAll: function () {
            loops.forEach(function (l) {
                if (l.paused) { l.paused = false; try { l.resume(); } catch (e) {} }
            });
        }
    };
    window.pauseWebGL = function () { window.WiehrLoops.pauseAll(); };
    window.resumeWebGL = function () { window.WiehrLoops.resumeAll(); };

    
    window.WIEHR_PERFORMANCE = name === 'mid' ? 'medium' : name;
})();
