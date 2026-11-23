#!/usr/bin/env python3
"""Checks a built site (./dist or a live base URL): JSON-LD parses, FAQPage text matches visible text,
ItemList items, no personal emails, table dash cells, title/description SERP length, favicon markup,
duplicate headings, and H1 words in the page text.
Usage: python3 scripts/check_site.py [dist|https://...] [paths...]"""
import sys, re, json, html, os, urllib.request
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from seo_width import title_px, desc_px, TITLE_MAX_PX, DESC_MAX_PX

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
    walk_root = src if not src.startswith('http') else 'dist'
    for d, _, fs in os.walk(walk_root):
        for f in fs:
            if f == 'index.html':
                paths.append('/' + os.path.relpath(d, walk_root).replace('.', '').strip('/') + ('/' if d != walk_root else ''))
    paths = sorted(set(p.replace('//', '/') for p in paths))

def norm(t): return re.sub(r'\s+', ' ', html.unescape(t)).strip()
def visible(h):
    h = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', h, flags=re.S)
    return norm(re.sub(r'<[^>]+>', '', h))

def attr(h, pattern):
    m = re.search(pattern, h, re.I | re.S)
    return html.unescape(m.group(1)) if m else ''

STOP = {
    'a', 'an', 'and', 'as', 'at', 'be', 'by', 'for', 'from', 'if', 'in', 'into', 'is', 'it',
    'of', 'on', 'or', 'the', 'to', 'vs', 'we', 'you', 'your', 'when', 'what', 'who', 'how',
    'why', 'with', 'our', 'this', 'that', 'are', 'was', 'were', 'not', 'its',
}

bad = 0; faqs = 0
personal = re.compile(r'danwyatt398|dthomas838485|@gmail\.com|@icloud\.com', re.I)
seen_favicon_files = False

if not src.startswith('http'):
    ico = os.path.join(src if src != 'dist' else 'dist', 'favicon.ico')
    # when src is 'dist'
    ico = os.path.join(ROOT, 'dist', 'favicon.ico') if src in ('dist', './dist') else os.path.join(src, 'favicon.ico')
    svg = os.path.join(os.path.dirname(ico), 'assets', 'favicon.svg')
    if not os.path.isfile(ico):
        print('MISSING FILE', ico); bad += 1
    if not os.path.isfile(svg):
        print('MISSING FILE', svg); bad += 1
    seen_favicon_files = True

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

    title = attr(h, r'<title>(.*?)</title>')
    desc = attr(h, r'<meta\s+name="description"\s+content="(.*?)"')
    if not desc:
        desc = attr(h, r'<meta\s+content="(.*?)"\s+name="description"')
    tw, dw = title_px(title), desc_px(desc)
    if tw > TITLE_MAX_PX:
        print(f'TITLE TOO WIDE {tw:.0f}px>{TITLE_MAX_PX} {p} {title}')
        bad += 1
    if dw > DESC_MAX_PX:
        print(f'DESC TOO WIDE {dw:.0f}px>{DESC_MAX_PX} {p} {desc[:140]}')
        bad += 1
    if not re.search(r'<link[^>]+rel=["\'][^"\']*icon', h, re.I):
        print('NO FAVICON MARKUP', p); bad += 1

    heads = re.findall(r'<h([1-6])\b[^>]*>(.*?)</h\1>', h, re.S | re.I)
    texts = [norm(re.sub(r'<[^>]+>', '', body)) for _, body in heads]
    for text, c in Counter(t for t in texts if t).items():
        if c > 1:
            print('DUP HEADING', p, c, text); bad += 1

    # Seobility flagged this on the homepage ("words from H1 heading not found in text").
    # Applied to '/' only: long guide/kit H1s are descriptive titles, not a homepage-style hook.
    if p == '/':
        h1s = [norm(re.sub(r'<[^>]+>', '', body)) for level, body in heads if level == '1']
        main = re.search(r'<main\b[^>]*>(.*?)</main>', h, re.S | re.I)
        main_html = main.group(1) if main else h
        main_wo_h1 = re.sub(r'<h1\b[^>]*>.*?</h1>', ' ', main_html, flags=re.S | re.I)
        body_vis = visible(main_wo_h1).lower()
        body_words = set(re.findall(r"[a-z0-9']+", body_vis))
        for h1 in h1s:
            missing = []
            for w in re.findall(r"[A-Za-z0-9']+", h1):
                lw = w.lower()
                if len(lw) <= 1 or lw in STOP:
                    continue
                if lw not in body_words:
                    missing.append(w)
            if missing:
                print('H1 WORDS NOT IN TEXT', p, missing, 'from', h1)
                bad += 1

print(f'Checked {len(paths)} pages, {faqs} FAQPage blocks, problems: {bad}')
sys.exit(1 if bad else 0)
