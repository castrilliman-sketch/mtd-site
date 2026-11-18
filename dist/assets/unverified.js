/* Pop-up for free-version products we have not yet checked on the provider's site.
   Progressive enhancement: without JS (or without <dialog> support) the links work as normal. */
(function () {
  if (typeof HTMLDialogElement === 'undefined') return;
  var dlg = document.getElementById('unverified-dialog');
  if (!dlg) return;
  var go = dlg.querySelector('[data-unverified-continue]');
  var closer = dlg.querySelector('[data-unverified-close]');
  if (!go || !closer) return;
  var last = null;

  document.querySelectorAll('a.unverified-link').forEach(function (a) {
    a.setAttribute('aria-haspopup', 'dialog');
  });

  function openFrom(a) {
    last = a;
    go.setAttribute('href', a.getAttribute('href') || '#');
    go.setAttribute('rel', a.getAttribute('rel') || 'noopener');
    if (a.getAttribute('target')) go.setAttribute('target', a.getAttribute('target'));
    else go.removeAttribute('target');
    if (!dlg.open) dlg.showModal();
  }

  function closeDlg() {
    if (dlg.open) dlg.close();
  }

  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a.unverified-link');
    if (!a || dlg.contains(a)) return;
    e.preventDefault();
    openFrom(a);
  });

  closer.addEventListener('click', closeDlg);
  go.addEventListener('click', function () { setTimeout(closeDlg, 0); });
  dlg.addEventListener('click', function (e) { if (e.target === dlg) closeDlg(); });
  dlg.addEventListener('close', function () {
    if (last && typeof last.focus === 'function') last.focus();
    last = null;
  });
})();
