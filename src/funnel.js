(function () {
  var form = document.getElementById('finder');
  var box = document.getElementById('matches');
  var dataEl = document.getElementById('finder-data');
  if (!form || !box || !dataEl) return;
  var data = JSON.parse(dataEl.textContent);
  var products = data.products || [];
  var total = data.total || products.length;
  var cards = box.querySelector('.pcards');
  var heading = box.querySelector('.matches-h');
  var note = box.querySelector('.matches-note');
  var more = box.querySelector('.matches-more');

  function selected() {
    return {
      who: (form.elements.who && form.elements.who.value) || '',
      want: (form.elements.want && form.elements.want.value) || '',
      keep: (form.elements.keep && form.elements.keep.value) || ''
    };
  }

  function isMatch(p, s) {
    if (s.who === 'landlord' && p.uk_property !== 'yes') return false;
    if (s.who === 'sole' && p.sole_trader !== 'yes') return false;
    if (s.who === 'both' && (p.uk_property !== 'yes' || p.sole_trader !== 'yes')) return false;
    if (s.want === 'free' && p.free_version !== 'yes') return false;
    if (s.want === 'low') {
      if (p.sort_price == null || p.sort_price <= 0 || p.sort_price > 10) return false;
    }
    if (s.want === 'full' && p.creates_records !== 'yes') return false;
    if (s.keep === 'spreadsheet' && p.bridging !== 'yes') return false;
    if ((s.keep === 'app' || s.keep === 'paper') && p.creates_records !== 'yes') return false;
    return true;
  }

  function sortMatches(a, b) {
    var ap = a.sort_price, bp = b.sort_price;
    var aMissing = ap == null, bMissing = bp == null;
    if (aMissing !== bMissing) return aMissing ? 1 : -1;
    if (!aMissing && ap !== bp) return ap - bp;
    return a.name.localeCompare(b.name);
  }

  function escapeHtml(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function card(p) {
    var price = p.price_text ? escapeHtml(p.price_text) : 'Price not yet checked';
    var tags = [];
    if (p.uk_property === 'yes') tags.push('Landlord');
    if (p.sole_trader === 'yes') tags.push('Self-employed');
    if (p.bridging === 'yes') tags.push('Spreadsheet');
    if (p.creates_records === 'yes') tags.push('App');
    if (p.free_version === 'yes') tags.push('Free version');
    var tagHtml = tags.slice(0, 4).map(function (t) { return '<span class="tag">' + escapeHtml(t) + '</span>'; }).join('');
    var label = p.aff ? 'View deal' : 'Visit site';
    return '<article class="pcard"><h3><a href="/software/' + escapeHtml(p.slug) + '/">' + escapeHtml(p.name) + '</a></h3>' +
      '<p class="pcard-price">' + price + '</p><p class="pcard-tags">' + tagHtml + '</p>' +
      '<div class="pcard-cta"><a class="btn" href="' + escapeHtml(p.href) + '" rel="' + escapeHtml(p.rel) + '" target="_blank" data-product="' + escapeHtml(p.slug) + '" data-aff="' + (p.aff ? 1 : 0) + '" data-cta="match" data-page="home">' + label + ' ↗</a>' +
      '<a class="pcard-more" href="/software/' + escapeHtml(p.slug) + '/">Details</a></div></article>';
  }

  function render(scroll) {
    var s = selected();
    if (!s.who && !s.want && !s.keep) {
      box.hidden = true;
      return;
    }
    var all = products.filter(function (p) { return isMatch(p, s); }).sort(sortMatches);
    var shown = all.slice(0, 5);
    box.hidden = false;
    if (!shown.length) {
      heading.textContent = 'No price-checked matches for that combination';
      note.textContent = 'Try another option, or browse the full list.';
      cards.innerHTML = '';
      more.innerHTML = '<a class="btn ghost" href="#directory">Compare all ' + total + ' products</a>';
    } else {
      heading.textContent = 'Matches what you picked';
      var extra = s.keep === 'paper' ? ' Paper records need to be kept digitally for MTD; these options create records in software.' : '';
      note.textContent = (all.length > shown.length ? 'Showing ' + shown.length + ' of ' + all.length + ' price-checked matches.' : all.length + ' price-checked match' + (all.length === 1 ? '.' : 'es.')) + extra;
      cards.innerHTML = shown.map(card).join('');
      more.innerHTML = '<a href="#directory">Compare all ' + total + ' products</a>';
    }
    if (scroll) box.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  form.addEventListener('change', function () { render(false); });
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    render(true);
  });
})();
