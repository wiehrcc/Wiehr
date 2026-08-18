(function () {
    'use strict';

    // Delegated so it covers .grabit buttons on any page, including any
    // rendered after load.
    function flash(btn) {
        var was = btn.getAttribute('data-label') || btn.textContent;
        btn.setAttribute('data-label', was);
        btn.textContent = 'COPIED';
        btn.classList.add('grabit-done');
        setTimeout(function () {
            btn.textContent = was;
            btn.classList.remove('grabit-done');
        }, 1200);
    }

    function legacy(text, btn) {
        var ta = document.createElement('textarea');
        ta.value = text;
        ta.setAttribute('readonly', '');
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        try { document.execCommand('copy'); flash(btn); } catch (e) {}
        document.body.removeChild(ta);
    }

    function copy(text, btn) {
        // navigator.clipboard needs a secure context. 127.0.0.1 counts, a LAN
        // IP does not, so keep the textarea path as a fallback.
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(text)
                .then(function () { flash(btn); })
                .catch(function () { legacy(text, btn); });
        } else {
            legacy(text, btn);
        }
    }

    document.addEventListener('click', function (e) {
        var btn = e.target.closest ? e.target.closest('.grabit') : null;
        if (!btn) return;
        e.preventDefault();
        e.stopPropagation();
        copy(btn.getAttribute('data-copy'), btn);
    });
})();
