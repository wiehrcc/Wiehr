(function() {
    'use strict';

    const LIGHT = 'light';
    const DARK = 'dark';
    const STORAGE_KEY = 'wiehr-theme';

    function getTheme() {
        return localStorage.getItem(STORAGE_KEY) || LIGHT;
    }

    function applyTheme(theme) {
        document.documentElement.setAttribute('data-wiehr-theme', theme);
        var bg = theme === DARK ? '#151617' : '#F4F4F4';
        document.documentElement.style.setProperty('background', bg, 'important');
        if (document.body) {
            document.body.style.setProperty('background', bg, 'important');
            document.body.style.color = theme === DARK ? '#f4f4f4' : '#151617';
        }
        var metaTheme = document.querySelector('meta[name="theme-color"]');
        if (metaTheme) metaTheme.content = theme === DARK ? '#151617' : '#f4f4f4';
        var icon = document.getElementById('lightnessicon');
        if (icon) icon.style.filter = theme === DARK ? 'invert(1)' : 'none';
    }

    function toggle() {
        var current = getTheme();
        var next = current === LIGHT ? DARK : LIGHT;
        localStorage.setItem(STORAGE_KEY, next);
        applyTheme(next);
        return next;
    }

    applyTheme(getTheme());

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() { applyTheme(getTheme()); });
    }

    window.WiehrTheme = {
        get: getTheme,
        set: function(t) { localStorage.setItem(STORAGE_KEY, t); applyTheme(t); },
        toggle: toggle,
        LIGHT: LIGHT,
        DARK: DARK
    };
})();
