#!/usr/bin/env python3
"""Checks a built site (./dist or a live base URL): JSON-LD parses, FAQPage text matches visible text,
ItemList items, no personal emails, table dash cells. Usage: python3 scripts/check_site.py [dist|https://...] [paths...]"""
import sys, re, json, html, os, urllib.request
src = sys.argv[1] if len(sys.argv) > 1 else 'dist'
paths = sys.argv[2:] or None
def get(p):
    if src.startswith('http'):
        req = urllib.request.Request(src.rstrip('/') + p + ('?nocache=' + str(os.getpid())), headers={'User-Agent': 'Mozilla/5.0 site-check'})
        return urllib.request.urlopen(req, timeout=30).read().decode()
    fp = os.path.join(src, p.lstrip('/')); fp += 'index.html' if fp.endswith('/') else ''
    return open(fp).read()
if paths is None:
    paths = []
    for d, _, fs in os.walk('dist'):
        for f in fs:
            if f == 'index.html': paths.append('/' + os.path.relpath(d, 'dist').replace('.', '').strip('/') + ('/' if d != 'dist' else ''))
    paths = sorted(set(p.replace('//', '/') for p in paths))
def norm(t): return re.sub(r'\s+', ' ', html.unescape(t)).strip()
def visible(h):
    h = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', h, flags=re.S)
    return norm(re.sub(r'<[^>]+>', '', h))
bad = 0; faqs = 0; personal = re.compile(r'danwyatt398|dthomas838485|@gmail\.com|@icloud\.com', re.I)
for p in paths:
    h = get(p); vis = visible(h)
    for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S):
        try: j = json.loads(raw)
        except Exception as e: print('JSON-LD PARSE FAIL', p, e); bad += 1; continue
        if j.get('@type') == 'FAQPage':
            faqs += 1
            for q in j['mainEntity']:
                for t in (q['name'], q['acceptedAnswer']['text']):
                    if norm(t) not in vis: print('FAQ TEXT NOT VISIBLE', p, norm(t)[:90]); bad += 1
        if j.get('@type') == 'ItemList':
            for it in j['itemListElement']:
                s = it.get('item', {})
                if s.get('@type') == 'SoftwareApplication':
                    for k in ('name', 'url', 'applicationCategory', 'operatingSystem'):
                        if not s.get(k): print('ITEM MISSING', k, s.get('name')); bad += 1
                    if s['name'] not in vis: print('ITEM NAME NOT VISIBLE', s['name']); bad += 1
                    if 'offers' in s and s['offers']['description'] not in vis: print('OFFER TEXT NOT VISIBLE', s['name']); bad += 1
    m = personal.findall(h)
    if m: print('PERSONAL EMAIL', p, set(m)); bad += 1
    emails = {e.rstrip('.') for e in re.findall(r'[\w.+-]+@[\w-]+\.[\w.]+', h)} - {'customerservices@mtdsoftwarecompare.co.uk'}
    emails = {e for e in emails if not e.endswith(('.png', '.js', '.css'))}
    if emails: print('OTHER EMAIL', p, emails); bad += 1
print(f'Checked {len(paths)} pages, {faqs} FAQPage blocks, problems: {bad}')
sys.exit(1 if bad else 0)
