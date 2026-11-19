#!/usr/bin/env python3
"""Private stats dashboard for the MTD site. Writes stats/index.html (NOT in dist/, never published).

Real data only. With no provider/site_id/token it renders an empty "no data yet" dashboard.

  GOATCOUNTER_TOKEN=xxxx python3 scripts/stats.py            # last 30 days
  GOATCOUNTER_TOKEN=xxxx python3 scripts/stats.py --days 7
  python3 scripts/stats.py --from 2026-12-01 --to 2026-12-31
  python3 scripts/stats.py --csv path/to/goatcounter-export.csv[.gz]   # use an export you downloaded yourself
  python3 scripts/stats.py --sample  # FAKE demo numbers to preview the layout; loudly labelled, writes stats/sample.html

Data source: GoatCounter's CSV export API (needs Settings -> Data collection -> "Individual pageviews" switched on),
which gives one row per page view/event with a random session ID, so page views, visitors, bounce, time on page and
click-through rate can all be computed here. Docs: https://www.goatcounter.com/help/api , https://www.goatcounter.com/help/export

Email sign-ups: form submissions come from the GoatCounter 'signup:<role>:<page>' event. Confirmed subscribers come from
Brevo's API when BREVO_API_KEY is set and config/email.json has provider "brevo" and list_id (read-only use:
GET /v3/contacts/lists/{id} and GET /v3/contacts/lists/{id}/contacts, https://developers.brevo.com/reference/get-list).

Affiliate earnings: put real figures exported from the affiliate networks in stats/earnings.csv
(columns: date,network,product_slug,clicks,sales,commission_gbp). Never type estimates into it.
"""
import argparse, csv, datetime as dt, gzip, html, io, json, os, random, re, sys, time, urllib.request, urllib.error
from collections import Counter, defaultdict
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = {k: v for k, v in json.load(open(f'{ROOT}/config/analytics.json')).items() if not k.startswith('_')}
SITE = json.load(open(f'{ROOT}/config/site.json'))
ECFG = {k: v for k, v in json.load(open(f'{ROOT}/config/email.json')).items() if not k.startswith('_')}
LON = ZoneInfo('Europe/London')
E = html.escape
OUT_DIR = f'{ROOT}/stats'
COUNTRIES = {'GB': 'United Kingdom', 'IE': 'Ireland', 'US': 'United States', 'DE': 'Germany', 'FR': 'France', 'NL': 'Netherlands',
             'ES': 'Spain', 'IN': 'India', 'CA': 'Canada', 'AU': 'Australia', 'PL': 'Poland', 'IT': 'Italy', 'PK': 'Pakistan',
             'NG': 'Nigeria', 'AE': 'United Arab Emirates', 'PT': 'Portugal', 'RO': 'Romania', 'JE': 'Jersey', 'GG': 'Guernsey', 'IM': 'Isle of Man'}
SEARCH = {'google': 'Google', 'bing': 'Bing', 'duckduckgo': 'DuckDuckGo', 'yahoo': 'Yahoo', 'ecosia': 'Ecosia', 'brave': 'Brave Search', 'yandex': 'Yandex', 'startpage': 'Startpage'}
AI = {'chatgpt': 'ChatGPT', 'openai': 'ChatGPT', 'perplexity': 'Perplexity', 'claude': 'Claude', 'anthropic': 'Claude', 'gemini': 'Gemini',
      'copilot': 'Copilot', 'grok': 'Grok', 'you.com': 'You.com', 'phind': 'Phind', 'deepseek': 'DeepSeek', 'mistral': 'Mistral'}
SOCIAL = {'reddit': 'Reddit', 'facebook': 'Facebook', 'fb.': 'Facebook', 't.co': 'X', 'twitter': 'X', 'x.com': 'X', 'linkedin': 'LinkedIn',
          'youtube': 'YouTube', 'instagram': 'Instagram', 'tiktok': 'TikTok', 'whatsapp': 'WhatsApp', 'mumsnet': 'Mumsnet', 'propertytribes': 'Property Tribes'}
FILTER_NAMES = {'free': 'Free version', 'bridging': 'Bridging (spreadsheets)', 'uk_property': 'Landlord (UK property)', 'sole_trader': 'Sole trader',
                'foreign_property': 'Foreign property', 'cis': 'CIS ready', 'tax_return': 'Files tax return too', 'joint': 'Joint property', 'checked': 'Price-checked'}

# ---------------- data fetching ----------------
def gc_export(code, token):
    api = f'https://{code}.goatcounter.com/api/v0'
    def req(method, path, data=None, raw=False):
        r = urllib.request.Request(api + path, method=method, data=json.dumps(data).encode() if data is not None else None,
                                   headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'})
        with urllib.request.urlopen(r, timeout=60) as resp:
            body = resp.read()
        return body if raw else json.loads(body or b'{}')
    exp = req('POST', '/export', {})
    for _ in range(120):
        info = req('GET', f'/export/{exp["id"]}')
        if info.get('finished_at'): break
        time.sleep(2)
    else:
        raise RuntimeError('GoatCounter export did not finish in 4 minutes')
    data = req('GET', f'/export/{exp["id"]}/download', raw=True)
    os.makedirs(f'{OUT_DIR}/data', exist_ok=True)
    open(f'{OUT_DIR}/data/goatcounter-export-latest.csv.gz', 'wb').write(data)
    return gzip.decompress(data).decode('utf-8') if data[:2] == b'\x1f\x8b' else data.decode('utf-8')

def read_csv_text(path):
    raw = open(path, 'rb').read()
    return gzip.decompress(raw).decode('utf-8') if raw[:2] == b'\x1f\x8b' else raw.decode('utf-8')

def parse_rows(text):
    rd = csv.reader(io.StringIO(text))
    header = next(rd)
    m = re.match(r'^(\d+),?(.*)$', header[0])          # GoatCounter writes the version before "Path", e.g. "2Path"
    if m and m.group(2) == '' and len(header) > 1 and header[1] == 'Path':
        header = [header[0] + header[1]] + header[2:]    # tolerate "2,Path" split into two cells
        m = re.match(r'^(\d+),?(.*)$', header[0])
    if not m or m.group(1) != '2':
        raise SystemExit(f'Unexpected GoatCounter export format {header[0]!r}; this script understands version 2 (see https://www.goatcounter.com/help/export).')
    cols = ['Path'] + header[1:]
    rows = []
    for r in rd:
        if not r: continue
        d = dict(zip(cols, r))
        if d.get('Bot', '0') not in ('0', ''): continue
        try:
            d['_t'] = dt.datetime.fromisoformat(d['Date'].replace('Z', '+00:00')).astimezone(LON)
        except Exception:
            continue
        d['_event'] = d.get('Event', '').lower() == 'true'
        rows.append(d)
    return rows

def sample_rows(start, end):
    """FAKE data for previewing the layout only."""
    rnd = random.Random(42)
    pages = ['/', '/do-i-need-mtd/', '/software/xero/', '/software/hammock-for-landlords/', '/software/freeagent/', '/software/quickbooks-intuit/', '/methodology/']
    refs = [('Google', 'g'), ('', ''), ('https://www.reddit.com/r/TaxUK/', 'h'), ('https://chatgpt.com/', 'h'), ('Bing', 'g'), ('https://www.propertytribes.com/', 'h')]
    rows = []
    days = (end - start).days + 1
    for i in range(days * 25):
        t = dt.datetime.combine(start + dt.timedelta(days=rnd.randrange(days)), dt.time(rnd.randrange(7, 23), rnd.randrange(60)), LON)
        sid = f's{i}'; ref = rnd.choice(refs); size = rnd.choice(['390,844,3', '1366,768,1', '1920,1080,1', '820,1180,2'])
        loc = rnd.choice(['GB'] * 9 + ['IE', 'US']); n = rnd.choice([1, 1, 2, 3])
        path = rnd.choice(pages)
        for j in range(n):
            base = dict(Session=sid, Browser='Chrome 131', System=rnd.choice(['iOS 18', 'Windows 11', 'Android 15', 'macOS 15']), Location=loc,
                        **{'Screen size': size}, Bot='0')
            tt = t + dt.timedelta(minutes=j * 2)
            rows.append(dict(base, Path=path, Title=path, _event=False, _t=tt, Referrer=ref[0] if j == 0 else '', **{'Referrer scheme': ref[1] if j == 0 else ''}))
            rows.append(dict(base, Path=f'time:{rnd.choice([5, 15, 30, 45, 60, 90, 120, 180])}:{path}', _event=True, _t=tt, Referrer='', **{'Referrer scheme': ''}))
            if path.startswith('/software/') and rnd.random() < .25:
                rows.append(dict(base, Path=f'out:site:{path.split("/")[2]}:{path}', _event=True, _t=tt, Referrer='', **{'Referrer scheme': ''}))
            if path in ('/', '/do-i-need-mtd/', '/software/xero/') and rnd.random() < .06:
                rows.append(dict(base, Path=f'signup:{rnd.choice(["landlord", "sole_trader", "both", "none", "accountant"])}:{path}', _event=True, _t=tt, Referrer='', **{'Referrer scheme': ''}))
            if path == '/' and rnd.random() < .3:
                rows.append(dict(base, Path=f'start:{rnd.choice(["uk_property", "sole_trader", "free", "bridging"])}:/', _event=True, _t=tt, Referrer='', **{'Referrer scheme': ''}))
                rows.append(dict(base, Path=f'filter:{rnd.choice(["free+uk_property", "cis+sole_trader", "bridging", "joint+uk_property"])}:/', _event=True, _t=tt, Referrer='', **{'Referrer scheme': ''}))
            path = rnd.choice(pages)
    return rows

# ---------------- analysis ----------------
def channel(ref, scheme):
    if not ref: return 'Direct / unknown', 'Direct / unknown'
    low = ref.lower()
    if scheme == 'c': return 'Campaign', ref
    host = urlsplit(ref).netloc.lower().removeprefix('www.') if scheme == 'h' or '://' in ref else low
    for k, v in AI.items():
        if k in low: return 'AI assistants', v
    for k, v in SEARCH.items():
        if k in low: return 'Search engines', v
    for k, v in SOCIAL.items():
        if k in low: return 'Social & forums', v
    if 'mail' in low: return 'Email', ref
    return 'Other websites', host or ref

def device(size):
    try:
        w = int(size.split(',')[0])
    except Exception:
        return 'Unknown'
    return 'Mobile' if w < 768 else 'Tablet' if w < 1100 else 'Desktop'

def split_event(path):
    """'out:aff:xero:/software/xero/' -> ('out', ['aff', 'xero'], '/software/xero/')"""
    i = path.find(':/')
    page = path[i + 1:] if i >= 0 else ''
    head = path[:i] if i >= 0 else path
    parts = head.split(':')
    return parts[0], parts[1:], page

def analyse(rows, start, end):
    rows = [r for r in rows if start <= r['_t'].date() <= end]
    pv = [r for r in rows if not r['_event'] and r['Path'].startswith('/')]
    ev = [r for r in rows if r['_event']]
    A = {'pageviews': len(pv), 'visitors': len({r['Session'] for r in pv}), 'events': len(ev)}
    sess_pv = Counter(r['Session'] for r in pv)
    interact = {r['Session'] for r in ev if split_event(r['Path'])[0] in ('out', 'start', 'filter', 'signup')}
    A['bounce'] = (sum(1 for s, n in sess_pv.items() if n == 1 and s not in interact) / len(sess_pv)) if sess_pv else None
    A['pages_per_visit'] = (len(pv) / len(sess_pv)) if sess_pv else None
    # daily
    daily = defaultdict(lambda: [0, set()])
    for r in pv:
        d = daily[r['_t'].date()]; d[0] += 1; d[1].add(r['Session'])
    A['daily'] = [(start + dt.timedelta(days=i), daily[start + dt.timedelta(days=i)][0], len(daily[start + dt.timedelta(days=i)][1])) for i in range((end - start).days + 1)]
    # per page
    pg = defaultdict(lambda: {'views': 0, 'visitors': set(), 'time': defaultdict(int), 'clickers': set(), 'clicks': 0, 'aff': 0, 'entr': 0})
    for r in pv:
        p = pg[r['Path']]; p['views'] += 1; p['visitors'].add(r['Session'])
    first = {}
    for r in sorted(pv, key=lambda r: r['_t']):
        first.setdefault(r['Session'], r)
    for r in first.values(): pg[r['Path']]['entr'] += 1
    prod = defaultdict(lambda: {'clicks': 0, 'aff': 0, 'clickers': set(), 'from': Counter()})
    outlinks = Counter(); starts = Counter(); filt = Counter(); combos = Counter(); searches = 0
    su_page = Counter(); su_role = Counter(); su_sess = set()
    for r in ev:
        kind, args, page = split_event(r['Path'])
        if kind == 'time' and args:
            try: pg[page]['time'][r['Session']] += int(args[0])
            except ValueError: pass
        elif kind == 'out' and len(args) >= 2:
            if args[0] in ('aff', 'site'):
                pr = prod[args[1]]; pr['clicks'] += 1; pr['aff'] += args[0] == 'aff'; pr['clickers'].add(r['Session']); pr['from'][page] += 1
                p = pg[page]; p['clicks'] += 1; p['aff'] += args[0] == 'aff'; p['clickers'].add(r['Session'])
            else:
                outlinks[args[1]] += 1
        elif kind == 'signup':
            su_page[page] += 1; su_role[(args[0] if args else 'none')] += 1; su_sess.add(r['Session'])
        elif kind == 'start' and args:
            starts[args[0]] += 1
        elif kind == 'filter' and args:
            fs = [f for f in args[0].split('+') if f and f != 'none']
            for f in fs: filt[f] += 1
            combos[' + '.join(FILTER_NAMES.get(f, f) for f in fs) or '(all filters cleared)'] += 1
            if 'search' in args[1:]: searches += 1
    alltimes = [t for p in pg.values() for t in p['time'].values()]
    A['avg_time'] = (sum(alltimes) / len(alltimes)) if alltimes else None
    A['time_samples'] = len(alltimes)
    A['pages'] = sorted(({'path': k, 'views': v['views'], 'visitors': len(v['visitors']), 'entries': v['entr'],
                          'avg_time': (sum(v['time'].values()) / len(v['time'])) if v['time'] else None,
                          'clicks': v['clicks'], 'aff': v['aff'],
                          'ctr': (len(v['clickers'] & v['visitors']) / len(v['visitors'])) if v['visitors'] else None}
                         for k, v in pg.items() if v['views']), key=lambda x: -x['views'])
    A['products'] = sorted(({'slug': k, 'clicks': v['clicks'], 'aff': v['aff'], 'people': len(v['clickers']),
                             'from': v['from'].most_common(3)} for k, v in prod.items()), key=lambda x: -x['clicks'])
    A['out_clicks'] = sum(p['clicks'] for p in A['products']); A['aff_clicks'] = sum(p['aff'] for p in A['products'])
    A['site_ctr'] = (len({r['Session'] for r in ev if split_event(r['Path'])[0] == 'out' and split_event(r['Path'])[1][:1] in (['aff'], ['site'])}) / A['visitors']) if A['visitors'] else None
    A['outlinks'] = outlinks.most_common(10)
    ch = Counter(); src = Counter()
    for r in first.values():
        c, s = channel(r.get('Referrer', ''), r.get('Referrer scheme', ''))
        ch[c] += 1; src[(c, s)] += 1
    A['channels'] = ch.most_common(); A['sources'] = src.most_common(15)
    A['devices'] = Counter(device(r.get('Screen size', '')) for r in first.values()).most_common()
    A['systems'] = Counter((r.get('System') or 'Unknown').split(' ')[0] for r in first.values()).most_common(6)
    A['countries'] = Counter(COUNTRIES.get((r.get('Location') or '')[:2], (r.get('Location') or 'Unknown')[:2] or 'Unknown') for r in first.values()).most_common(10)
    A['signups'] = sum(su_page.values()); A['signup_roles'] = su_role.most_common()
    A['signup_rate'] = (len(su_sess) / A['visitors']) if A['visitors'] else None
    A['signup_pages'] = [(pgp, n, len(pg[pgp]['visitors']) if pgp in pg else 0) for pgp, n in su_page.most_common(10)]
    A['starts'] = starts.most_common(); A['filters'] = filt.most_common(); A['combos'] = combos.most_common(8); A['searches'] = searches
    return A

def brevo_signups(start, end):
    """Confirmed subscribers from Brevo (read-only). Returns dict or a string explaining why there's no data."""
    if ECFG.get('provider') != 'brevo':
        return 'Email sign-up isn\'t switched on yet (config/email.json has no provider), so there are no subscribers.'
    key = os.environ.get('BREVO_API_KEY', '').strip(); lid = str(ECFG.get('list_id') or '').strip()
    if not lid: return 'Set <code>list_id</code> in <code>config/email.json</code> to your Brevo list ID to show confirmed subscribers.'
    if not key: return 'Run with <code>BREVO_API_KEY=…</code> set to load confirmed subscribers from Brevo.'
    def get(path):
        r = urllib.request.Request('https://api.brevo.com/v3' + path, headers={'api-key': key, 'accept': 'application/json'})
        return json.load(urllib.request.urlopen(r, timeout=30))
    try:
        lst = get(f'/contacts/lists/{lid}')
        new, roles, off = 0, Counter(), 0
        since = dt.datetime.combine(start, dt.time(0), LON).astimezone(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')
        while True:
            page = get(f'/contacts/lists/{lid}/contacts?limit=500&offset={off}&modifiedSince={since}')
            cs = page.get('contacts', [])
            for c in cs:
                try: cd = dt.datetime.fromisoformat(c.get('createdAt', '').replace('Z', '+00:00')).astimezone(LON).date()
                except ValueError: continue
                if start <= cd <= end:
                    new += 1; roles[(c.get('attributes') or {}).get(ECFG.get('fields', {}).get('role', 'MTD_ROLE')) or 'Not given'] += 1
            off += len(cs)
            if len(cs) < 500 or off >= page.get('count', 0): break
        return {'total': lst.get('totalSubscribers'), 'blacklisted': lst.get('totalBlacklisted'), 'new': new, 'roles': roles.most_common()}
    except Exception as e:
        return f'Could not read Brevo: {E(str(e))[:200]}'

def earnings(start, end):
    path = f'{OUT_DIR}/earnings.csv'
    if not os.path.exists(path): return None
    rows = []
    for r in csv.DictReader(open(path)):
        try:
            d = dt.date.fromisoformat(r['date'])
        except Exception:
            continue
        if start <= d <= end: rows.append(r)
    tot = Counter(); by = defaultdict(Counter)
    for r in rows:
        for k in ('clicks', 'sales', 'commission_gbp'):
            try: v = float(r.get(k) or 0)
            except ValueError: v = 0
            tot[k] += v; by[(r.get('network', ''), r.get('product_slug', ''))][k] += v
    return {'tot': tot, 'by': sorted(by.items(), key=lambda x: -x[1]['commission_gbp'])}

# ---------------- rendering ----------------
CSS = """:root{--ink:#14213d;--muted:#5b6475;--line:#dfe3ea;--bg:#f6f7f9;--brand:#0b6e4f;--warn:#fff7e0}
*{box-sizing:border-box}body{margin:0;font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;color:var(--ink);background:var(--bg)}
.wrap{max-width:1180px;margin:0 auto;padding:18px}header{display:flex;justify-content:space-between;align-items:flex-end;flex-wrap:wrap;gap:8px;margin-bottom:6px}
h1{margin:0;font-size:1.6rem}h1 span{color:var(--brand)}h2{font-size:1.05rem;margin:0 0 10px}.muted{color:var(--muted);font-size:.88rem}
.banner{border-radius:10px;padding:14px 16px;margin:12px 0;font-size:.95rem}.empty{background:#eef3fb;border:1px solid #c9d8f0}.sample{background:#ffe9e9;border:2px solid #d33;font-weight:700;color:#8a1010}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin:14px 0}
.kpi{background:#fff;border:1px solid var(--line);border-radius:10px;padding:14px}.kpi small{display:block;color:var(--muted);font-size:.8rem;text-transform:uppercase;letter-spacing:.04em}
.kpi b{font-size:1.7rem;display:block;margin-top:2px}.kpi b.na{color:#a0a7b4;font-size:1.25rem}.kpi i{font-style:normal;color:var(--muted);font-size:.78rem}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:14px}.card{background:#fff;border:1px solid var(--line);border-radius:10px;padding:16px;overflow:auto}
.card.wide{grid-column:1/-1}table{width:100%;border-collapse:collapse;font-size:.9rem}th,td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line)}
th{font-size:.78rem;color:var(--muted);text-transform:uppercase;letter-spacing:.03em}td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
.none{color:#8a93a3;font-style:italic;padding:18px 0;text-align:center}.bar{height:8px;background:var(--brand);border-radius:4px;opacity:.75}
ol.steps li{margin:4px 0}code{background:#f0f2f5;padding:1px 5px;border-radius:4px}svg{display:block}
@media(max-width:600px){.grid{grid-template-columns:1fr}}"""

def fmt_n(x): return '—' if x is None else f'{x:,}'
def fmt_pct(x): return '—' if x is None else f'{x * 100:.1f}%'
def fmt_s(x):
    if x is None: return '—'
    x = round(x); return f'{x // 60}m {x % 60:02d}s' if x >= 60 else f'{x}s'

def table(head, rows, empty):
    if not rows: return f'<div class="none">{empty}</div>'
    th = ''.join(f'<th class="{"n" if i else ""}">{E(h)}</th>' for i, h in enumerate(head))
    tr = ''.join('<tr>' + ''.join(f'<td class="{"n" if i else ""}">{c}</td>' for i, c in enumerate(r)) + '</tr>' for r in rows)
    return f'<table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table>'

def share_rows(items, total):
    return [(E(str(k)), f'{v:,}', f'<div style="display:flex;align-items:center;gap:6px;justify-content:flex-end"><div class="bar" style="width:{max(2, int(80 * v / total))}px"></div>{v / total * 100:.0f}%</div>') for k, v in items] if total else []

def chart(daily):
    if not daily or not any(v for _, v, _ in daily): return '<div class="none">No visits recorded in this date range yet.</div>'
    W, H, n = 1100, 160, len(daily); mx = max(v for _, v, _ in daily) or 1; bw = W / n
    bars = ''.join(f'<rect x="{i * bw + 1:.1f}" y="{H - 18 - (v / mx) * (H - 30):.1f}" width="{max(bw - 2, 1):.1f}" height="{(v / mx) * (H - 30):.1f}" fill="#0b6e4f" opacity=".75"><title>{d:%a %d %b}: {v} page views, {u} visitors</title></rect>' for i, (d, v, u) in enumerate(daily))
    lab = f'<text x="0" y="{H - 3}" font-size="11" fill="#5b6475">{daily[0][0]:%d %b}</text><text x="{W}" y="{H - 3}" font-size="11" fill="#5b6475" text-anchor="end">{daily[-1][0]:%d %b}</text><text x="0" y="10" font-size="11" fill="#5b6475">max {mx} views/day</text>'
    return f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Page views per day">{bars}{lab}</svg>'

def render(A, start, end, state, note, earn, brevo=None):
    now = dt.datetime.now(LON)
    empty = A is None
    A = A or {}
    g = lambda k: A.get(k)
    nd = 'No data yet'
    banner = {'empty': f'<div class="banner empty"><strong>No data yet.</strong> {note}</div>',
              'sample': '<div class="banner sample">⚠ SAMPLE DATA – these numbers are made up to preview the layout. They are NOT real visits, clicks or earnings.</div>',
              'live': f'<div class="banner empty" style="background:#eef6f2;border-color:#cfe5da">Real data from {E(note)}.</div>'}[state]
    def kpi(label, val, hint=''):
        return f'<div class="kpi"><small>{label}</small><b class="{"na" if empty else ""}">{nd if empty else val}</b><i>{hint}</i></div>'
    kpis = ''.join([kpi('Visitors', fmt_n(g('visitors')), 'unique visits (random session ID)'), kpi('Page views', fmt_n(g('pageviews'))),
                    kpi('Avg engaged time / page', fmt_s(g('avg_time')), f'from {fmt_n(g("time_samples"))} page visits' if not empty else 'active, visible time'),
                    kpi('Pages per visit', '—' if g('pages_per_visit') is None else f'{g("pages_per_visit"):.2f}'),
                    kpi('Bounce rate', fmt_pct(g('bounce')), 'one page, no clicks'),
                    kpi('"Visit site" clicks', fmt_n(g('out_clicks')), f'{fmt_n(g("aff_clicks"))} on affiliate links' if not empty else 'clicks to software providers'),
                    kpi('Click-through rate', fmt_pct(g('site_ctr')), 'visitors who clicked to a provider')])
    pages = [(f'<code>{E(p["path"])}</code>', fmt_n(p['views']), fmt_n(p['visitors']), fmt_n(p['entries']), fmt_s(p['avg_time']), fmt_n(p['clicks']), fmt_n(p['aff']), fmt_pct(p['ctr'])) for p in (g('pages') or [])[:25]]
    prods = [(E(p['slug']), fmt_n(p['clicks']), fmt_n(p['aff']), fmt_n(p['people']), ', '.join(f'<code>{E(a)}</code> ({b})' for a, b in p['from'])) for p in (g('products') or [])]
    vis = sum(v for _, v in (g('channels') or [])) or 0
    starts = [(E(k.replace('+', ' + ')), f'{v:,}') for k, v in (g('starts') or [])]
    filt = [(E(FILTER_NAMES.get(k, k)), f'{v:,}') for k, v in (g('filters') or [])]
    combos = [(E(k), f'{v:,}') for k, v in (g('combos') or [])]
    if earn:
        t = earn['tot']
        earn_html = (f'<p><b>£{t["commission_gbp"]:,.2f}</b> commission from {t["sales"]:,.0f} sales ({t["clicks"]:,.0f} clicks counted by the networks) in this period. Source: <code>stats/earnings.csv</code>.</p>'
                     + table(['Network / product', 'Network clicks', 'Sales', 'Commission'], [(E(f'{a} / {b}'), f'{v["clicks"]:,.0f}', f'{v["sales"]:,.0f}', f'£{v["commission_gbp"]:,.2f}') for (a, b), v in earn['by']], 'No rows in range.'))
    else:
        earn_html = ('<div class="none">No earnings data yet – no affiliate programme has been joined.</div><p class="muted">Once you are accepted (QuickBooks via FlexOffers, Xero via PartnerStack, Sage via Impact, Zoho), '
                     'export each network\'s performance report and add the real figures to <code>stats/earnings.csv</code> with columns '
                     '<code>date,network,product_slug,clicks,sales,commission_gbp</code>. FlexOffers, PartnerStack and Impact all have reporting APIs, so this can be automated later with your API keys. '
                     'Only confirmed figures from the networks go here – never estimates.</p>')
    rl = {'landlord': 'Landlord', 'sole_trader': 'Sole trader', 'both': 'Both', 'accountant': 'Accountant', 'none': 'Not given'}
    sp = [(f'<code>{E(a)}</code>', f'{n:,}', f'{v:,}', fmt_pct(n / v if v else None)) for a, n, v in (g('signup_pages') or [])]
    sr = [(E(rl.get(k, k)), f'{v:,}') for k, v in (g('signup_roles') or [])]
    if isinstance(brevo, dict):
        bh = (f'<p><b>{fmt_n(brevo["new"])}</b> new confirmed subscribers in this period · <b>{fmt_n(brevo["total"])}</b> on the list in total'
              f' ({fmt_n(brevo["blacklisted"])} unsubscribed or blocked). Confirmation rate: '
              f'{fmt_pct(brevo["new"] / g("signups") if g("signups") else None)} of form submissions. Source: Brevo API.</p>'
              + table(['"I am a…" (confirmed, this period)', 'Subscribers'], [(E(str(k)), f'{v:,}') for k, v in brevo['roles']], 'No new confirmed subscribers in this period.'))
    else:
        bh = f'<p class="muted">Confirmed subscribers: {brevo or "not loaded."}</p>'
    signup_html = (f'<div class="kpis" style="margin-top:0">{kpi("Form submissions", fmt_n(g("signups")), "people who sent the form (before confirming)")}'
                   f'{kpi("Sign-up rate", fmt_pct(g("signup_rate")), "visitors who sent the form")}</div>'
                   + table(['Page the form was sent from', 'Submissions', 'Page visitors', 'Conversion'], sp, nd)
                   + table(['"I am a…" answer (submissions)', 'Submissions'], sr, '') + bh)
    _n = SITE["name"]
    if " " in _n:
        _lead, _accent = _n.rsplit(" ", 1)
        LOGO = f'{E(_lead)} <span>{E(_accent)}</span>'
    else:
        LOGO = f'<span>{E(_n)}</span>'
    return f'''<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>Private stats – {E(SITE["name"])}</title><style>{CSS}</style></head><body><div class="wrap">
<header><div><h1>{LOGO} · private stats</h1>
<div class="muted">{start:%d %b %Y} – {end:%d %b %Y} (UK time) · generated {now:%d %b %Y, %H:%M} UK time · provider: {E(CFG.get("provider") or "not set")}</div></div>
<div class="muted">Private: this file is not part of the published site.</div></header>
{banner}
<div class="kpis">{kpis}</div>
<div class="grid">
<div class="card wide"><h2>Page views per day</h2>{chart(g("daily")) if not empty else '<div class="none">No data yet.</div>'}</div>
<div class="card wide"><h2>Top pages</h2>{table(["Page", "Views", "Visitors", "Entrances", "Avg time", "Visit-site clicks", "Affiliate clicks", "Click-through"], pages, nd)}
<p class="muted">Click-through = share of a page's visitors who clicked a "Visit …" button to a software provider. This is the conversion rate that drives affiliate income.</p></div>
<div class="card wide"><h2>"Visit site" clicks per product</h2>{table(["Product", "Clicks", "Affiliate clicks", "People", "Top pages clicked from"], prods, nd)}</div>
<div class="card"><h2>Where visitors came from</h2>{table(["Channel", "Visits", "Share"], share_rows(g("channels") or [], vis), nd)}</div>
<div class="card"><h2>Top referrers / search sources</h2>{table(["Source", "Channel", "Visits"], [(E(s), E(c), f"{v:,}") for (c, s), v in (g("sources") or [])], nd)}</div>
<div class="card"><h2>Devices</h2>{table(["Device", "Visits", "Share"], share_rows(g("devices") or [], vis), nd)}{table(["Operating system", "Visits", "Share"], share_rows(g("systems") or [], vis), "") if not empty else ""}</div>
<div class="card"><h2>Countries</h2>{table(["Country", "Visits", "Share"], share_rows(g("countries") or [], vis), nd)}</div>
<div class="card"><h2>"Start here" buttons</h2>{table(["Button (preset)", "Clicks"], starts, nd)}</div>
<div class="card"><h2>Filter usage</h2>{table(["Filter", "Times switched on"], filt, nd)}{table(["Most-used combinations", "Times"], combos, "") if not empty else ""}
<p class="muted">{"" if empty else f"Search box used {g('searches'):,} times (we never record what was typed). "}</p></div>
<div class="card"><h2>Other outbound links</h2>{table(["Website", "Clicks"], [(E(h), f"{v:,}") for h, v in (g("outlinks") or [])], nd)}</div>
<div class="card wide"><h2>Email sign-ups (Free MTD Ready Kit)</h2>{signup_html}</div>
<div class="card wide"><h2>Affiliate earnings</h2>{earn_html}</div>
</div>
<p class="muted">Avg engaged time counts only seconds when the tab was visible and the visitor had scrolled, clicked or typed in the last minute, so it is usually lower than "time on page" in Google Analytics. Bots are excluded. Visitors are counted by GoatCounter's random session ID (resets after 8 hours), not cookies.</p>
</div></body></html>'''

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--days', type=int, default=30); ap.add_argument('--from', dest='frm'); ap.add_argument('--to')
    ap.add_argument('--csv'); ap.add_argument('--sample', action='store_true'); ap.add_argument('--out')
    a = ap.parse_args()
    end = dt.date.fromisoformat(a.to) if a.to else dt.datetime.now(LON).date()
    start = dt.date.fromisoformat(a.frm) if a.frm else end - dt.timedelta(days=a.days - 1)
    os.makedirs(OUT_DIR, exist_ok=True)
    out = a.out or (f'{OUT_DIR}/sample.html' if a.sample else f'{OUT_DIR}/index.html')
    token = os.environ.get('GOATCOUNTER_TOKEN', '').strip()
    prov, code = CFG.get('provider'), CFG.get('site_id')
    A, state, note = None, 'empty', ''
    if a.sample:
        A, state = analyse(sample_rows(start, end), start, end), 'sample'
    elif a.csv:
        A, state, note = analyse(parse_rows(read_csv_text(a.csv)), start, end), 'live', f'GoatCounter export file {os.path.basename(a.csv)}'
    elif not prov or not code:
        note = 'Analytics isn\'t switched on yet, so nothing has been collected. To start: (1) create a free GoatCounter account and pick a site code; (2) put <code>"provider": "goatcounter"</code> and <code>"site_id": "&lt;your code&gt;"</code> in <code>config/analytics.json</code>, rebuild and publish; (3) in GoatCounter, switch on Settings → Data collection → "Individual pageviews" and create an API key (read/export permission); (4) run <code>GOATCOUNTER_TOKEN=… python3 scripts/stats.py</code>.'
    elif prov != 'goatcounter':
        note = f'Provider "{E(prov)}" is set, but this dashboard script only knows how to read GoatCounter so far.'
    elif not token:
        note = f'Tracking is configured for GoatCounter site <code>{E(code)}</code>, but no API token was given. Run with <code>GOATCOUNTER_TOKEN=…</code> set to load real numbers.'
    else:
        try:
            A, state, note = analyse(parse_rows(gc_export(code, token)), start, end), 'live', f'GoatCounter ({code}.goatcounter.com)'
        except urllib.error.HTTPError as e:
            msg = e.read().decode('utf-8', 'replace')[:300]
            note = f'Could not read GoatCounter (HTTP {e.code}): {E(msg)}. If it mentions individual pageviews, switch on Settings → Data collection → "Individual pageviews".'
        except Exception as e:
            note = f'Could not read GoatCounter: {E(str(e))}'
    if state == 'live' and A and A['pageviews'] == 0 and A['events'] == 0:
        A, state, note = None, 'empty', f'Connected to {E(note)}, but nothing was recorded between {start:%d %b} and {end:%d %b %Y}.'
    brevo = brevo_signups(start, end) if state != 'sample' else 'sample mode (Brevo not contacted).'
    open(out, 'w').write(render(A, start, end, state, note, earnings(start, end) if state != 'sample' else None, brevo))
    print(f'Wrote {out} ({state})')

if __name__ == '__main__':
    main()
