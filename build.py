#!/usr/bin/env python3
"""Build the static MTD software directory into ./dist. No dependencies beyond Python 3."""
import json, re, html, shutil, os, datetime, sys
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from seo_width import fit_title, fit_desc, title_ok, choose_title, repeated_words, title_words
DIST = os.path.join(ROOT, 'dist')
SITE = json.load(open(f'{ROOT}/config/site.json'))
_ACFG = os.environ.get('MTD_ANALYTICS_CONFIG', f'{ROOT}/config/analytics.json')
ANALYTICS = {k: v for k, v in json.load(open(_ACFG)).items() if not k.startswith('_')}
ANALYTICS_ON = bool(ANALYTICS.get('provider') and ANALYTICS.get('site_id'))
AFF = {k: v for k, v in json.load(open(f'{ROOT}/config/affiliates.json')).items() if not k.startswith('_')}
_ECFG = os.environ.get('MTD_EMAIL_CONFIG', f'{ROOT}/config/email.json')
EMAIL = {k: v for k, v in json.load(open(_ECFG)).items() if not k.startswith('_')}
EMAIL_ON = bool(EMAIL.get('provider') and EMAIL.get('form_action'))
DL = json.load(open(f'{ROOT}/data/deadlines.json'))
KIT_PDF, KIT_ICS = '/kit/mtd-ready-kit-2026-28.pdf', '/kit/mtd-deadlines-2026-28.ics'
HM = json.load(open(f'{ROOT}/data/raw/hmrc-products.json'))
VV = json.load(open(f'{ROOT}/data/vendor-verified.json'))
CHECKED = VV['checked']
HMRC_DATE = HM['retrieved']
BASE = SITE['base_url'].rstrip('/')
NAME = SITE['name']
ELIGIBILITY_URL = 'https://www.gov.uk/guidance/find-out-if-and-when-you-need-to-use-making-tax-digital-for-income-tax'
OG_IMAGE = BASE + '/assets/og-image.png'
LOGO_URL = BASE + '/assets/apple-touch-icon.png'
OPERATOR = (SITE.get('operator_name') or '').strip() or 'Daniel Wyatt'
OPERATOR_ORG = (SITE.get('operator_org') or '').strip() or 'CastilliAI'
OPERATOR_ORG_URL = (SITE.get('operator_org_url') or '').strip() or 'https://www.castilliai.com/'
CONTACT_EMAIL = (SITE.get('contact_email') or '').strip()
FINDER = 'https://www.tax.service.gov.uk/find-making-tax-digital-income-tax-software/'
E = html.escape

def logo_html():
    """Wordmark: last word in the brand colour."""
    if ' ' in NAME:
        lead, _, accent = NAME.rpartition(' ')
        return f'{E(lead)} <span>{E(accent)}</span>'
    return f'<span>{E(NAME)}</span>'


def contact_html():
    if CONTACT_EMAIL:
        addr = E(CONTACT_EMAIL)
        return f'<a href="mailto:{addr}">{addr}</a>'
    return 'Contact email coming soon'

def operator_org_link(label=None):
    """A followed (dofollow) link to the operator's organisation."""
    return f'<a href="{E(OPERATOR_ORG_URL)}">{E(label or OPERATOR_ORG)}</a>'

def parent_org_ld():
    return {'@type': 'Organization', 'name': OPERATOR_ORG, 'url': OPERATOR_ORG_URL}

def person_ld():
    return {
        '@context': 'https://schema.org',
        '@type': 'Person',
        'name': OPERATOR,
        'url': BASE + '/about/',
        'jobTitle': 'Founder',
        'worksFor': parent_org_ld(),
        'sameAs': [OPERATOR_ORG_URL],
    }

def organization_ld():
    org = {
        '@context': 'https://schema.org',
        '@type': 'Organization',
        'name': NAME,
        'url': BASE + '/',
        'logo': LOGO_URL,
        'parentOrganization': parent_org_ld(),
    }
    if CONTACT_EMAIL:
        org['email'] = CONTACT_EMAIL
    return org


def nice_date(iso):
    d = datetime.date.fromisoformat(iso); return f'{d.day} {d.strftime("%B %Y")}'

def slugify(s):
    s = s.lower().replace('&', ' and ').replace('@', 'at ')
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')

def clean_url(u):
    if not u: return None
    u = html.unescape(u)
    p = urlsplit(u)
    q = [(k, v) for k, v in parse_qsl(p.query) if not k.lower().startswith('utm_') and k != 'rs']
    return urlunsplit((p.scheme, p.netloc.lower(), p.path, urlencode(q), ''))

TR_ITEMS = ['UK interest', 'Employment (PAYE)', 'UK dividends', 'State Pension income', 'Private pension incomes',
            'Partner income from a partnership', 'Foreign dividends', 'Foreign interest', 'Private pension contributions',
            'Construction Industry Scheme', 'Charitable giving', 'Capital Gains', 'Student Loan', 'Marriage Allowance',
            'Voluntary Class 2 National Insurance', 'High Income Child Benefit Charge']
ST = {'Ready now': 'yes', 'In development': 'in development', 'Not included': 'no'}

# ---------- merge data ----------
products = []
seen = set()
for r in HM['products']:
    f = r['features']; summ = r['summary']
    slug = slugify(r['name'])
    while slug in seen: slug += '-2'
    seen.add(slug)
    v = VV['products'].get(r['name'], {})
    st = lambda k: ST.get(f.get(k), 'unknown')
    p = {
        'name': r['name'], 'slug': slug, 'on_hmrc_list': True,
        'hmrc_url': r['hmrc_url'], 'hmrc_retrieved': HMRC_DATE,
        'website': clean_url(r['website']),
        'free_version': 'yes' if st('Free version') == 'yes' else ('no' if f else 'unknown'),
        'creates_records': st('Software that creates digital records'),
        'bridging': st('Bridging software that connects to records'),
        'sole_trader': st('Sole trader'), 'uk_property': st('UK property'), 'foreign_property': st('Foreign property'),
        'submits': summ.get('Submission type', 'unknown'),
        'cis': st('Construction Industry Scheme'),
        'vat': st('Making Tax Digital for VAT'),
        'hmrc_assist': st('HMRC Assist (Submission Feedback)'),
        'individual': st('Individual software'), 'agent': st('Agent software'),
        'standard_period': st('Standard update period (6 April to 5 April)'),
        'calendar_period': st('Calendar update period (1 April to 31 March)'),
        'accessibility': {k: st(k) for k in ['Blindness or impaired vision', 'Deafness or impaired hearing', 'Motor or physical difficulties', 'Cognitive impairments']},
        'tax_return_items': {k: st(k) for k in TR_ITEMS},
        'software_type': ' and '.join(o for o in ['Web browser', 'Desktop application'] if o in r['specs'].get('Software type', '')) or 'unknown',
        'compatible_with': ', '.join(o for o in ['Microsoft Windows', 'Mac OS', 'Linux'] if o in r['specs'].get('Compatible with', '')) or 'unknown',
        'language': r['specs'].get('Language', 'unknown'),
        'price_text': v.get('price_text', 'unknown'), 'price_note': v.get('price_note'),
        'price_from_gbp_month': v.get('price_from_gbp_month'), 'price_from_gbp_year': v.get('price_from_gbp_year'),
        'price_source': v.get('price_source'), 'price_checked': (v.get('price_checked') or CHECKED) if v else None,
        'joint_property': v.get('joint', 'unknown'), 'joint_source': v.get('joint_source'),
        'affiliate_programme': v.get('affiliate', {'status': 'unknown'}),
        'affiliate_url': AFF.get(slug, ''),
        'vendor_checked': bool(v),
    }
    p['tax_return'] = 'Tax return' in p['submits']
    if p['price_from_gbp_month'] is not None: p['sort_price'] = p['price_from_gbp_month']
    elif p['price_from_gbp_year'] is not None: p['sort_price'] = round(p['price_from_gbp_year'] / 12, 2)
    else: p['sort_price'] = None
    products.append(p)
products.sort(key=lambda p: p['name'].lower().strip('"#@'))
BY = {p['slug']: p for p in products}

def az_name(p):
    return p['name'].lower().strip('"#@')

def is_free_variant(p):
    """True for the free listing of a paid/free pair (slug X-free with a matching X)."""
    s = p['slug']
    return s.endswith('-free') and s[:-5] in BY

def pair_counterpart(p):
    """The other product in a paid/free pair, or None."""
    s = p['slug']
    if s.endswith('-free') and s[:-5] in BY:
        return BY[s[:-5]]
    return BY.get(s + '-free')

FEATURED_NAMES = json.load(open(f'{ROOT}/config/featured.json'))['products']
_missing_feat = [n for n in FEATURED_NAMES if n not in {p['name'] for p in products}]
assert not _missing_feat, f'config/featured.json names not on HMRC list: {_missing_feat}'
for p in products: p['featured'] = p['name'] in FEATURED_NAMES
FEATURED = [p for p in products if p['featured']]
FEATURED.sort(key=lambda p: (is_free_variant(p), az_name(p)))
CHECKEDP = [p for p in products if p['vendor_checked']]
CHECKEDP.sort(key=lambda p: (not p['featured'], is_free_variant(p), az_name(p)))

def dir_key(p):
    """Default directory order: featured first, then price-checked, paid plans before free variants, then A-Z."""
    return (not p['featured'], not p['vendor_checked'], is_free_variant(p), az_name(p))

# ---------- product-page indexing (config/indexing.json) ----------
IDX = {k: v for k, v in json.load(open(f'{ROOT}/config/indexing.json')).items() if not k.startswith('_')}
_unknown_idx = [s for s in IDX.get('always_index', []) + IDX.get('release_for_indexing', []) + IDX.get('hold_noindex', []) if s not in BY]
if _unknown_idx: raise SystemExit(f'config/indexing.json: unknown product slugs {_unknown_idx}')
def _verified_with_notes(p):
    v = VV['products'].get(p['name'], {})
    return bool(v.get('price_text') and v['price_text'] != 'unknown' and v.get('price_source') and v.get('price_note'))
INDEXABLE = {p['slug'] for p in products
             if p['slug'] not in set(IDX.get('hold_noindex', []))
             and (p['slug'] in set(IDX.get('always_index', []) + IDX.get('release_for_indexing', []))
                  or (IDX.get('auto_index_verified', True) and _verified_with_notes(p)))}

# ---------- helpers ----------
def link_for(p):
    """Return (href, rel, is_affiliate). Affiliate links get rel=sponsored nofollow."""
    if p['affiliate_url']:
        return p['affiliate_url'], 'sponsored nofollow noopener', True
    return p['website'] or p['hmrc_url'], 'noopener', False

def outbound_cta(p, kind='visit', cls='btn', page='', label=None):
    """Single affiliate-ready outbound button. Falls back to the official URL."""
    href, rel, aff = link_for(p)
    if label is None:
        label = f'View {p["name"]} deal' if aff else f'Visit {p["name"]}'
    attrs = [f'class="{cls}"', f'href="{E(href)}"', f'rel="{rel}"', 'target="_blank"',
             f'data-product="{E(p["slug"])}"', f'data-aff="{int(aff)}"', f'data-cta="{E(kind)}"']
    if page:
        attrs.append(f'data-page="{E(page)}"')
    return f'<a {" ".join(attrs)}>{E(label)} ↗</a>'

def card_price(p):
    if p.get('price_text') and p['price_text'] != 'unknown':
        return E(p['price_text'])
    return 'Price not yet checked'

def product_card(p, kind='visit'):
    tags = []
    if p['uk_property'] == 'yes': tags.append('Landlord')
    if p['sole_trader'] == 'yes': tags.append('Self-employed')
    if p['bridging'] == 'yes': tags.append('Spreadsheet')
    if p['creates_records'] == 'yes': tags.append('App')
    if p['free_version'] == 'yes': tags.append('Free version')
    tag_html = ''.join(f'<span class="tag">{E(t)}</span>' for t in tags[:4])
    return (
        f'<article class="pcard">'
        f'<p class="pcard-name"><a href="/software/{E(p["slug"])}/">{E(p["name"])}</a></p>'
        f'<p class="pcard-price">{card_price(p)}</p>'
        f'<p class="pcard-tags">{tag_html}</p>'
        f'<div class="pcard-cta">{outbound_cta(p, kind=kind, cls="btn", page="home")}'
        f'<a class="pcard-more" href="/software/{E(p["slug"])}/">More about {E(p["name"])}</a></div>'
        + ('<p class="disclose aff-note">Affiliate link. <a href="/affiliate-disclosure/">Disclosure</a></p>' if link_for(p)[2] else '') +
        f'</article>'
    )

def featured_card(p):
    facts = []
    inc = incomes(p)
    if inc: facts.append(', '.join(inc))
    facts.append('Updates + tax return' if p['tax_return'] else 'Quarterly updates only')
    if p['bridging'] == 'yes': facts.append('Works with spreadsheets')
    if p['free_version'] == 'yes': facts.append('Free version (HMRC)')
    if p['cis'] == 'yes': facts.append('CIS on tax return')
    if p['joint_property'] == 'yes': facts.append('Joint property splits')
    fl = ''.join(f'<li>{E(x)}</li>' for x in facts[:5])
    return (f'<article class="pcard fcard"><p class="pcard-name"><a href="/software/{E(p["slug"])}/">{E(p["name"])}</a></p>'
            f'<p class="pcard-price">{card_price(p)}</p><ul class="ffacts">{fl}</ul>'
            f'<div class="pcard-cta">{outbound_cta(p, kind="featured", cls="btn", page="home")}'
            f'<a class="pcard-more" href="/software/{E(p["slug"])}/">More about {E(p["name"])}</a></div>'
            + ('<p class="disclose aff-note">Affiliate link. <a href="/affiliate-disclosure/">Disclosure</a></p>' if link_for(p)[2] else '') +
            '</article>')

def finder_payload():
    items = []
    for p in CHECKEDP:
        href, rel, aff = link_for(p)
        items.append({
            'slug': p['slug'], 'name': p['name'],
            'price_text': p['price_text'] if p['price_text'] != 'unknown' else '',
            'sort_price': p['sort_price'],
            'free_version': p['free_version'], 'bridging': p['bridging'],
            'creates_records': p['creates_records'], 'uk_property': p['uk_property'],
            'sole_trader': p['sole_trader'], 'href': href, 'rel': rel, 'aff': aff,
            'featured': p['featured'],
            'free_variant': is_free_variant(p),
        })
    return json.dumps({'total': len(products), 'products': items}, ensure_ascii=False)

POPULAR_SLUGS = ['xero', 'quickbooks-intuit', 'freeagent', 'sage-sole-trader-and-landlord', 'zoho']

def aff_row_note():
    return '<p class="disclose">Some Visit buttons may be affiliate links; we may earn a commission if you sign up. <a href="/affiliate-disclosure/">How we make money</a>.</p>'


def yn(v, short=False):
    m = {'yes': ('Yes', 'y'), 'no': ('No', 'n'), 'in development': ('In development', 'd'), 'unknown': ('Unknown', 'u'),
         'paid plans only': ('Paid plans only', 'd')}
    t, c = m.get(v, (v, ''))
    return f'<span class="{c}">{t}</span>'

def incomes(p):
    out = [lbl for k, lbl in [('sole_trader', 'Sole trader'), ('uk_property', 'UK property'), ('foreign_property', 'Foreign property')] if p[k] == 'yes']
    return out

def types(p):
    t = []
    if p['creates_records'] == 'yes': t.append('Records')
    if p['bridging'] == 'yes': t.append('Bridging')
    return t

def dash(label):
    """Subtle dash for an empty table cell, with an accessible label and hover title."""
    return f'<span class="u dash" title="{E(label)}"><span aria-hidden="true">–</span><span class="sr">{E(label)}</span></span>'

def price_html(p):
    if p['price_text'] == 'unknown':
        return '<span class="u">Not yet checked</span>'
    return E(p['price_text'])

def cell_yn(v, label='Not yet checked'):
    return dash(label) if v == 'unknown' else yn(v)

def analytics_tag():
    """Nothing at all is added unless config/analytics.json has provider + site_id."""
    if not ANALYTICS_ON: return ''
    opts = {k: v for k, v in ANALYTICS.items() if k not in ('provider', 'site_id')}
    return (f'\n<script src="/assets/analytics.js" defer data-mtd-provider="{E(ANALYTICS["provider"])}" '
            f'data-mtd-site="{E(ANALYTICS["site_id"])}" data-mtd-opts="{E(json.dumps(opts))}"></script>')

VERIFY = {k: (v or '').strip() for k, v in json.load(open(f'{ROOT}/config/verification.json')).items() if not k.startswith('_')}
def verification_tags(path):
    """Google Search Console / Bing ownership meta tags (homepage only, only when set in config/verification.json)."""
    if path != '/': return ''
    t = ''
    if VERIFY.get('google_site_verification'): t += f'\n<meta name="google-site-verification" content="{E(VERIFY["google_site_verification"])}">'
    if VERIFY.get('bing_msvalidate'): t += f'\n<meta name="msvalidate.01" content="{E(VERIFY["bing_msvalidate"])}">'
    return t

def head(title, desc, path, jsonld=(), noindex=False, og_type='website'):
    canon = BASE + path
    title, desc = fit_title(title), fit_desc(desc)
    blocks = [organization_ld(), *jsonld]
    ld = ''.join(f'<script type="application/ld+json">{json.dumps(j, ensure_ascii=False)}</script>' for j in blocks)
    robots = '<meta name="robots" content="noindex,follow">' if noindex else '<meta name="robots" content="index,follow,max-snippet:-1">'
    return f'''<!doctype html><html lang="en-GB"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title><meta name="description" content="{E(desc)}">
<link rel="canonical" href="{canon}">{robots}{verification_tags(path)}
<meta property="og:type" content="{E(og_type)}"><meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:url" content="{canon}"><meta property="og:site_name" content="{E(NAME)}"><meta property="og:locale" content="en_GB">
<meta property="og:image" content="{OG_IMAGE}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="{E(NAME + ' — ' + SITE['tagline'])}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{OG_IMAGE}"><meta name="twitter:title" content="{E(title)}"><meta name="twitter:description" content="{E(desc)}">
<meta name="theme-color" content="#0b6e4f">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/assets/favicon-32.png" type="image/png" sizes="32x32">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="stylesheet" href="/assets/style.css">{ld}{analytics_tag()}</head><body>
<a class="skip" href="#main">Skip to content</a>
<header class="site"><div class="wrap"><a class="logo" href="/">{logo_html()}</a>
<nav class="main" aria-label="Main"><a href="/#directory">Compare software</a><a href="/do-i-need-mtd/">Do I need MTD?</a><a href="/guides/">Guides</a><a href="/methodology/">How we check</a><a href="/founders-blog/">Founders Blog</a><a href="/about/">About</a><a class="navkit" href="/free-mtd-kit/">Free MTD kit</a></nav></div></header>
<main id="main">'''

def foot():
    return f'''</main><footer class="site"><div class="wrap"><div class="cols3">
<div><strong>{E(NAME)}</strong><br>{E(SITE['tagline'])}.<br>HMRC list last read: {nice_date(HMRC_DATE)}.<p class="project">{operator_org_link('A ' + OPERATOR_ORG + ' project')}</p></div>
<nav class="fnav" aria-label="Footer"><a href="/#directory">Compare all software</a><a href="/do-i-need-mtd/">Do I need MTD, and when?</a><a href="/guides/">MTD guides</a><a href="/methodology/">Methodology</a><a href="/free-mtd-kit/">Free MTD Ready Kit</a></nav>
<nav class="fnav" aria-label="About this site"><a href="/about/">About</a><a href="/founders-blog/">Founders Blog</a><a href="/affiliate-disclosure/">Affiliate disclosure</a><a href="/privacy/">Privacy</a><span class="contact">{contact_html()}</span></nav></div>
<p class="disclaimer"><strong>Not tax advice.</strong> This site gives general information only. It is not tax, legal or financial advice. Check your own position on <a href="{ELIGIBILITY_URL}">GOV.UK</a> or with a qualified adviser before you act. HMRC does not recommend any software product and is not connected with this site. Prices change, so always confirm on the provider's own website. No affiliate links are live yet. If we add any, they'll be clearly labelled; see our <a href="/affiliate-disclosure/">disclosure</a>. Contains public sector information licensed under the <a href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/">Open Government Licence v3.0</a>.</p>
</div></footer></body></html>'''

def write(path, content):
    fp = os.path.join(DIST, path.lstrip('/'))
    if fp.endswith('/'): fp += 'index.html'
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    open(fp, 'w').write(content)

def faq_ld(qas):
    return {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': re.sub('<[^>]+>', '', a)}} for q, a in qas]}

def faq_html(qas):
    return ''.join(f'<details><summary>{E(q)}</summary><p>{a}</p></details>' for q, a in qas)

def crumb_ld(items):
    return {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': BASE + u} for i, (n, u) in enumerate(items)]}

DATES_HTML = (
    '<div class="dates">'
    '<div class="date"><strong>6 April 2026</strong>Qualifying income over £50,000 (2024 to 2025 tax year)</div>'
    '<div class="date"><strong>6 April 2027</strong>Qualifying income over £30,000 (2025 to 2026 tax year)</div>'
    '<div class="date"><strong>6 April 2028</strong>Qualifying income over £20,000 (2026 to 2027 tax year)</div></div>'
    f'<p class="disclose">Source: <a href="{ELIGIBILITY_URL}">GOV.UK, Find out if and when you need to use Making Tax Digital for Income Tax</a>. Qualifying income is your self-employment plus property income before expenses.</p>'
)

# ---------- email sign-up (Free MTD Ready Kit) ----------
def next_deadline():
    today = datetime.date.today()
    for e in DL['events']:
        if e['kind'] == 'update' and datetime.date.fromisoformat(e['date']) >= today:
            return e
    return None

def kit_points():
    """What's in the kit. Reminder emails are only listed when a real sign-up form is configured."""
    checklist = ('Getting-ready checklist', 'From "do I need it?" to your first quarterly update, in plain English.')
    if EMAIL_ON:
        return [
            ('Deadline calendar, 2026 to 2028', 'Every quarterly update, tax return and payment date on one page, plus a calendar file for Google, Apple or Outlook.'),
            checklist,
            ('Reminder emails', 'A short email 7 days before every HMRC deadline, so nothing slips.'),
        ]
    return [
        ('Deadline calendar, 2026 to 2028', 'Every quarterly update, tax return and payment date on one page.'),
        checklist,
        ('Calendar file', 'Add every date to Google, Apple or Outlook, with an alert 7 days before.'),
    ]

CONSENT = ("We'll email you the kit, a reminder before each MTD deadline and occasional plain-English MTD tips. "
           "Some tips may mention software we earn a commission from; we always say so. Unsubscribe in one click, any time. "
           "We never sell or share your details.")

def download_kit(uid, variant):
    """Shown while no email provider is configured: direct PDF and calendar downloads, no email collected."""
    return f'''<div class="signup-download {variant}" aria-labelledby="{uid}-h">
<p class="downloads"><a class="btn big" href="{KIT_PDF}" download>Download the kit (PDF)</a> <a class="btn big ghost" href="{KIT_ICS}" download>Add all deadlines to my calendar (.ics)</a></p>
<p class="consent">No email address needed. The calendar file works with Google Calendar (Settings, then Import), Apple Calendar and Outlook. Each date has an alert 7 days before. Optional email reminders are not available yet. <a href="/privacy/#email">Privacy</a>.</p>
</div>'''

def signup_form(uid, variant):
    if not EMAIL_ON:
        return download_kit(uid, variant)
    f = EMAIL.get('fields', {}); rv = EMAIL.get('role_values', {})
    live = EMAIL_ON
    dis = '' if live else ' disabled'
    roles = ''.join(f'<label class="pill"><input type="radio" name="{E(f.get("role", "MTD_ROLE"))}" value="{E(rv.get(k, lbl))}" data-k="role" data-role="{k}"{dis}><span>{lbl}</span></label>'
                    for k, lbl in [('landlord', 'Landlord'), ('sole_trader', 'Sole trader'), ('both', 'Both'), ('accountant', 'Accountant')])
    hidden = ''
    if live:
        hp = EMAIL.get('honeypot_field', '')
        for k, v in EMAIL.get('hidden_fields', {}).items():
            if k == hp:
                hidden += f'<div class="hp" aria-hidden="true"><label>Leave this empty <input type="text" name="{E(k)}" value="" tabindex="-1" autocomplete="off" data-hp></label></div>'
            else:
                hidden += f'<input type="hidden" name="{E(k)}" value="{E(str(v))}">'
    action = f' action="{E(EMAIL["form_action"])}" method="post" data-live="1"' if live else ' action="#" onsubmit="return false" data-live="0"'
    btn = 'Send me the free kit' if live else 'Opening soon'
    soon = '' if live else '<p class="signup-soon"><strong>Sign-ups open very soon.</strong> The kit is ready; we\'re just switching on the email service. Nothing you type here is sent.</p>'
    return f'''<form class="signup-form {variant}"{action} aria-labelledby="{uid}-h">
{soon}<div class="sf-row"><label class="sf"><span>First name</span><input type="text" name="{E(f.get("first_name", "FIRSTNAME"))}" data-k="first_name" autocomplete="given-name" maxlength="60" required{dis}></label>
<label class="sf"><span>Email address</span><input type="email" name="{E(f.get("email", "EMAIL"))}" autocomplete="email" maxlength="120" required{dis}></label></div>
<fieldset class="roles"><legend>I am a… <span class="opt">(optional, so reminders fit your situation)</span></legend>{roles}</fieldset>
{hidden}<button type="submit" class="btn big"{dis}>{btn}</button>
<p class="consent">{CONSENT} <a href="/privacy/#email">How we use your email</a>.</p>
<p class="signup-msg" role="alert"></p>
</form>
<div class="signup-ok" hidden tabindex="-1"><strong>Nearly there, <span class="signup-name"></span>!</strong>
<p>We've sent you an email. Click the <b>confirm</b> button in it and your kit arrives straight away. Can't see it in a couple of minutes? Check your spam or promotions folder.</p></div>'''

def signup_script():
    return '<script src="/assets/signup.js" defer></script>' if EMAIL_ON else ''

def nd_line():
    nd = next_deadline()
    return f'<p class="nextdl">Next HMRC deadline: <b>{nice_date(nd["date"])}</b>, {E(nd["title"][0].lower() + nd["title"][1:])}.</p>' if nd else ''

def signup_block(variant):
    """variant: 'home' (full section after Start here), 'inline' (short box on guide/product pages)."""
    uid = f'kit-{variant}'
    if variant == 'inline':
        if EMAIL_ON:
            blurb = 'Get the 2026 to 2028 deadline calendar, a getting-ready checklist and an email reminder 7 days before every HMRC deadline. Free.'
        else:
            blurb = 'Download the 2026 to 2028 deadline calendar, a getting-ready checklist and a calendar file with an alert 7 days before every HMRC deadline. Free.'
        return f'''<aside class="signup inline" id="{uid}"><div class="si-text"><p class="eyebrow">Free MTD Ready Kit</p>
<h2 id="{uid}-h">Never miss an MTD deadline</h2>
<p>{blurb} <a href="/free-mtd-kit/">What's in the kit</a></p></div>
{signup_form(uid, 'compact')}</aside>{signup_script()}'''
    pts = ''.join(f'<li><b>{E(a)}</b> {E(b)}</li>' for a, b in kit_points())
    if EMAIL_ON:
        lead = 'Four quarterly updates a year, plus your tax return. After your first year, four late-submission penalty points mean a £200 penalty. Get every date, a checklist, and a reminder before each one.'
    else:
        lead = 'Four quarterly updates a year, plus your tax return. After your first year, four late-submission penalty points mean a £200 penalty. Download every date, a checklist, and a calendar file with an alert 7 days before each deadline.'
    return f'''<section class="signup home" id="{uid}"><div class="wrap"><div class="sh-grid">
<div class="sh-text"><p class="eyebrow">Free MTD Ready Kit</p><h2 id="{uid}-h">Never miss a Making Tax Digital deadline</h2>
<p class="lead">{lead}</p>
<ul class="ticks">{pts}</ul>{nd_line()}
<p class="disclose">Every date is from GOV.UK. <a href="/free-mtd-kit/">See what's inside</a></p></div>
<div class="sh-form">{signup_form(uid, 'full')}</div>
</div></div></section>{signup_script()}'''

def kit_pages():
    pts = ''.join(f'<div class="kp"><h3>{E(a)}</h3><p>{E(b)}</p></div>' for a, b in kit_points())
    if EMAIL_ON:
        faq = [
            ('Is it really free?', 'Yes. There\'s nothing to pay and no card details. The site is paid for by affiliate commissions, which we always label.'),
            ('What emails will I get?', 'The kit straight away, then three short emails over the next fortnight to help you get ready, a reminder 7 days before each quarterly update and tax return deadline (around 5 or 6 a year), and occasional MTD news when HMRC changes something important.'),
            ('Why do you ask "I am a…"?', 'It\'s optional. It lets us leave out reminders that don\'t apply to you, for example landlord-only points if you\'re a sole trader.'),
            ('Will you pass my details to anyone?', 'No. We never sell or share your details. Our email service stores them for us under contract. If we ever offer to put you in touch with an accountant, that will be a separate request you choose to make.'),
            ('Can I unsubscribe?', 'Yes, with one click at the bottom of every email. We then stop emailing you straight away.'),
            ('Is this tax advice?', 'No. It\'s general information taken from GOV.UK, with links to every source. Check your own position on GOV.UK or with a qualified adviser.'),
        ]
        titles = [
            'Free Making Tax Digital kit: dates, checklist and reminders',
            'Free Making Tax Digital kit: calendar and checklist',
            f'Free Making Tax Digital kit | {NAME}',
        ]
        desc = 'Free MTD kit: every Income Tax deadline for 2026 to 2028, a getting-ready checklist, a calendar file and reminders 7 days before each deadline.'
        h1 = 'Every MTD deadline, a clear checklist, and a reminder before each one'
        lead = 'Making Tax Digital for Income Tax means four quarterly updates a year as well as your tax return. Get every date in one place and an email 7 days before each deadline. Free.'
        trust = '<span>✓ Every date from GOV.UK</span> <span>✓ No card, no spam</span> <span>✓ Unsubscribe in one click</span>'
    else:
        faq = [
            ('Is it really free?', 'Yes. There\'s nothing to pay, no card details and no email address needed. The site is paid for by affiliate commissions, which we always label.'),
            ('How do I get the kit?', 'Download the PDF and the calendar file from this page. They start downloading straight away.'),
            ('What is the calendar file?', 'It adds every deadline to Google Calendar, Apple Calendar or Outlook, with an alert 7 days before each date. In Google Calendar, open Settings, then Import.'),
            ('Will you email me reminders?', 'Not yet. The calendar file already has a 7-day alert for each date. If we later offer optional email reminders, this page will explain how to sign up, and you will not be added to a list automatically.'),
            ('Is this tax advice?', 'No. It\'s general information taken from GOV.UK, with links to every source. Check your own position on GOV.UK or with a qualified adviser.'),
        ]
        titles = [
            'Free Making Tax Digital kit: dates, checklist and calendar',
            'Free Making Tax Digital kit: checklist and calendar file',
            f'Free Making Tax Digital kit | {NAME}',
        ]
        desc = 'Free MTD kit: every Income Tax deadline for 2026 to 2028, a getting-ready checklist, and a calendar file with an alert 7 days before each deadline.'
        h1 = 'Every MTD deadline and a clear checklist, ready to download'
        lead = 'Making Tax Digital for Income Tax means four quarterly updates a year as well as your tax return. Download every date in one PDF, plus a calendar file with an alert 7 days before each deadline. Free.'
        trust = '<span>✓ Every date from GOV.UK</span> <span>✓ No sign-up needed</span> <span>✓ Free to download</span>'
    out = head(choose_title(titles), fit_desc(desc),
               '/free-mtd-kit/', [faq_ld(faq), crumb_ld([('Home', '/'), ('Free MTD Ready Kit', '/free-mtd-kit/')])])
    out += f'''<section class="kit-hero"><div class="wrap"><div class="kh-grid">
<div class="kh-text"><p class="eyebrow">Free MTD Ready Kit · 2026 to 2028</p>
<h1>{h1}</h1>
<p class="lead">{lead}</p>
<ul class="ticks">{''.join(f'<li><b>{E(a)}</b> {E(b)}</li>' for a, b in kit_points())}</ul>
{nd_line()}
<p class="trust">{trust}</p></div>
<div class="kh-form" id="get"><h2 id="kit-page-h">Get your free kit</h2>{signup_form('kit-page', 'full')}</div>

</div></div></section>
<div class="wrap" style="max-width:980px">
<h2>What's in the kit</h2><div class="kps">{pts}</div>
<div class="previews"><figure><img src="/assets/kit-preview-1.png" width="794" height="1123" alt="Kit page 1: when you start, what MTD means you do, penalties" loading="lazy"><figcaption>Page 1: your start date and what MTD involves</figcaption></figure>
<figure><img src="/assets/kit-preview-2.png" width="794" height="1123" alt="Kit page 2: quarterly update calendar for 2026 to 2027 and 2027 to 2028" loading="lazy"><figcaption>Page 2: the quarterly update calendar</figcaption></figure></div>
<p>The 5-page PDF also has every key date in order (updates, tax returns, payments on account and start dates), a getting-ready checklist, a routine for each quarter and year end, and links to every GOV.UK source. The calendar file adds each date to your calendar with an alert 7 days before.</p>
<h2>Who it's for</h2>
<ul><li><b>Landlords and sole traders</b> already using MTD since April 2026, or starting in April 2027 or April 2028.</li>
<li><b>Anyone not sure yet</b> whether they need MTD. Page 1 shows the thresholds, and our <a href="/do-i-need-mtd/">plain-English guide</a> explains them.</li>
<li><b>Accountants and bookkeepers</b> who want a clean calendar to share with clients.</li></ul>
<h2>Questions</h2>{faq_html(faq)}
<p style="margin:28px 0"><a class="btn big" href="#get">Get the free kit</a></p>
</div>{signup_script()}'''
    out += foot()
    write('/free-mtd-kit/', out)
    # Brevo: "confirmation page after clicking the validation link" -> /free-mtd-kit/confirmed/
    out = head(choose_title([
        'Your Making Tax Digital ready kit is available to download',
        'Your Making Tax Digital kit is ready to download',
    ]), 'Download the Free MTD Ready Kit.', '/free-mtd-kit/confirmed/', noindex=True)
    out += f'''<div class="wrap" style="max-width:760px"><h1>You're in. Here's your MTD Ready Kit</h1>
<p class="lead">Thanks for confirming. We've also emailed you these links so you can find them later.</p>
<p class="downloads"><a class="btn big" href="{KIT_PDF}" download>Download the kit (PDF)</a> <a class="btn big ghost" href="{KIT_ICS}" download>Add all deadlines to my calendar (.ics)</a></p>
<p class="disclose">The calendar file works with Google Calendar (Settings, then Import), Apple Calendar and Outlook. Each date has an alert 7 days before.</p>
<h2>What next</h2><ol><li>Check when you start: <a href="/do-i-need-mtd/">Do I need MTD, and when?</a></li><li>Find software that fits: <a href="/#directory">compare all {len(products)} HMRC-recognised products</a>.</li>
<li>Look out for our next email in a couple of days: the 5 decisions to make before your first quarterly update.</li></ol></div>'''
    out += foot(); write('/free-mtd-kit/confirmed/', out)
    # Brevo: "confirmation page after submitting the form" (used when JavaScript is off) -> /free-mtd-kit/check-your-inbox/
    out = head(choose_title([
        f'Check your inbox to confirm the kit | {NAME}',
        f'Check your inbox | {NAME}',
    ]), 'Confirm your email to get the Free MTD Ready Kit.', '/free-mtd-kit/check-your-inbox/', noindex=True)
    out += '''<div class="wrap" style="max-width:760px"><h1>Check your inbox</h1>
<p class="lead">We've sent you an email. Click the <b>confirm</b> button in it and your Free MTD Ready Kit arrives straight away.</p>
<p>Can't see it after a couple of minutes? Check your spam or promotions folder, or <a href="/free-mtd-kit/">try again</a> in case of a typo.</p></div>'''
    out += foot(); write('/free-mtd-kit/check-your-inbox/', out)

def software_ld_item(p):
    """SoftwareApplication for the homepage ItemList. Offers only when a price is verified in vendor-verified.json."""
    it = {'@type': 'SoftwareApplication', 'name': p['name'], 'url': f'{BASE}/software/{p["slug"]}/',
          'applicationCategory': 'FinanceApplication', 'operatingSystem': 'Web' if 'Web browser' in p['software_type'] else (p['compatible_with'] if p['compatible_with'] != 'unknown' else 'Web')}
    price = p['price_from_gbp_month'] if p['price_from_gbp_month'] is not None else p['price_from_gbp_year']
    if price is not None and p.get('price_source'):
        it['offers'] = {'@type': 'Offer', 'price': f'{price:.2f}', 'priceCurrency': 'GBP', 'url': p['price_source'], 'description': p['price_text']}
    return it

# ---------- homepage ----------
def home():
    n = len(products)
    free_checked = [p for p in CHECKEDP if p['sort_price'] == 0 or p['free_version'] == 'yes']
    rows = {True: [], False: []}
    # Default order: featured group first, then 'Best of the rest'; price-checked first, paid before free variants, then A-Z (matches directory.js).
    for p in sorted(products, key=dir_key):
        href, rel, aff = link_for(p)
        inc = incomes(p)
        aud = ('i' if p['individual'] == 'yes' else '') + ('a' if p['agent'] == 'yes' else '')
        sp = p['sort_price'] if p['sort_price'] is not None else 99999
        data = {
            'name': E(p['name'].lower()), 'free': int(p['free_version'] == 'yes'), 'bridging': int(p['bridging'] == 'yes'),
            'uk_property': int(p['uk_property'] == 'yes'), 'sole_trader': int(p['sole_trader'] == 'yes'),
            'foreign_property': int(p['foreign_property'] == 'yes'), 'cis': int(p['cis'] == 'yes'), 'tax_return': int(p['tax_return']),
            'joint': int(p['joint_property'] == 'yes'), 'calendar': int(p['calendar_period'] == 'yes'), 'checked': int(p['vendor_checked']), 'aud': aud, 'group': 'featured' if p['featured'] else 'rest',
            'free-variant': int(is_free_variant(p)),
            's-name': E(p['name'].lower().strip('"#@')), 's-price': sp, 's-free': int(p['free_version'] != 'yes'),
            's-cis': {'yes': 0, 'in development': 1}.get(p['cis'], 2), 's-joint': {'yes': 0, 'paid plans only': 1}.get(p['joint_property'], 2),
        }
        attrs = ' '.join(f'data-{k}="{v}"' for k, v in data.items())
        rows[p['featured']].append(f'''<tr {attrs}{' class="rest"' if not p['featured'] else ''}><td class="name" data-label="Software"><a href="/software/{p['slug']}/">{E(p['name'])}</a>{' <span class="tag f">Featured</span>' if p['featured'] else ''}{' <span class="tag v" title="Price checked on the provider site">price-checked</span>' if p['vendor_checked'] else ''}</td>
<td data-label="Price (from)">{E(p['price_text']) if p['price_text'] != 'unknown' else dash('Price not yet checked')}</td><td data-label="Free version">{cell_yn(p['free_version'], 'Not listed by HMRC')}</td>
<td data-label="Type">{' '.join(f'<span class="tag">{t}</span>' for t in types(p)) or dash('Not listed by HMRC')}</td>
<td data-label="Income sources">{', '.join(inc) or dash('Not listed by HMRC')}</td>
<td data-label="Submits">{'Updates + tax return' if p['tax_return'] else 'Quarterly updates only'}</td>
<td data-label="CIS on tax return">{cell_yn(p['cis'], 'Not listed by HMRC')}</td><td data-label="Joint property">{cell_yn(p['joint_property'], 'Joint property not yet checked')}</td></tr>''')
    free_list = ''.join(f'<li><a href="/software/{p["slug"]}/">{E(p["name"])}</a>: {E(p["price_text"])}{" – " + E(p["price_note"]) if p.get("price_note") else ""}</li>' for p in free_checked)
    qas = [
        ("Does HMRC provide free software for Making Tax Digital?", "HMRC's guidance says you, or an agent, will need to use commercial software that works with Making Tax Digital for Income Tax. It also says free products are available for people with simple tax affairs, but they may have limits, such as a set number of transactions. <a href=\"https://www.gov.uk/guidance/choose-the-right-software-for-making-tax-digital-for-income-tax\">Source: GOV.UK, Choose the right software</a>"),
        ("What is MTD bridging software?", "Bridging software connects to records you already keep, such as a spreadsheet, and sends your quarterly updates to HMRC. Some bridging products also submit your tax return; others only send the updates. Use the 'Bridging (spreadsheets)' filter above to see them, or read <a href=\"/guides/mtd-spreadsheets-bridging-software/\">our guide to spreadsheets and bridging software</a>."),
        ("Can I use more than one MTD product?", "Yes. HMRC says you can use more than one product, but only one product for each separate submission. For example, a landlord cannot use two products to send the same property quarterly update. If you combine products, make sure together they cover your quarterly updates and your tax return. <a href=\"https://www.gov.uk/guidance/choose-the-right-software-for-making-tax-digital-for-income-tax\">Source: GOV.UK, Choose the right software</a>"),
        ("When are MTD quarterly updates due?", "For both standard and calendar update periods, the deadlines are 7 August, 7 November, 7 February and 7 May (the following tax year). <a href=\"https://www.gov.uk/guidance/use-making-tax-digital-for-income-tax/send-quarterly-updates\">Source: GOV.UK, Send quarterly updates</a>. For what happens if one is late, see <a href=\"/guides/mtd-late-quarterly-update-penalties/\">MTD penalty points explained</a>. For how the two period types differ, see <a href=\"/guides/mtd-standard-vs-calendar-update-periods/\">standard vs calendar update periods</a>."),
        ("Does HMRC recommend any MTD software?", "No. HMRC says it does not recommend any product or software provider. Every product in this directory has been through HMRC's recognition process. We show our featured products first, because we may earn a commission from them (see our affiliate disclosure), then every other product under Best of the rest. Within each group, price-checked products come first, paid plans before their free variants, then A to Z. You can still filter, including to free versions only. Right now no affiliate links are live, so a commission does not change this order."),
        ("Why does a product say 'Quarterly updates only'?", "HMRC lists some products as able to send quarterly updates but not to submit your tax return. If you pick one of those, you'll need another product, or an agent, for the tax return after the year ends."),
    ]
    il = {'@context': 'https://schema.org', '@type': 'ItemList', 'name': 'HMRC-recognised MTD for Income Tax software we have price-checked',
          'numberOfItems': len(CHECKEDP), 'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'item': software_ld_item(p)} for i, p in enumerate(CHECKEDP)]}
    web = {'@context': 'https://schema.org', '@type': 'WebSite', 'name': NAME, 'url': BASE + '/', 'inLanguage': 'en-GB'}
    any_aff = any(link_for(p)[2] for p in products)
    popular = [BY[s] for s in POPULAR_SLUGS if s in BY]
    popular_html = "".join(product_card(p, kind="popular") for p in popular)
    out = head(choose_title([
        f"Compare {n} HMRC-recognised Making Tax Digital products",
        f"Compare {n} HMRC-recognised Making Tax Digital apps today",
        f"Compare {n} HMRC-recognised Making Tax Digital apps",
    ]),
               f"Compare {n} HMRC-recognised MTD software products. Pick who you are and what you need. Prices checked at source.",
               "/", [web, il, faq_ld(qas)])
    out += f'''<section class="hero funnel"><div class="wrap">
<h1>Find your MTD software in 30 seconds</h1>
<p class="sub">Answer three quick questions and find your MTD software in 30 seconds. {n} HMRC-recognised products are listed below.</p>
<p class="hero-cta"><a class="btn big" href="#finder">Find my software</a> <a class="hero-link" href="/do-i-need-mtd/">Do I need MTD?</a></p>
<h2 class="picks-h">Popular picks</h2>
<div class="pcards row" id="popular">{popular_html}</div>
<form class="finder" id="finder" action="/#directory" method="get">
<p class="finder-label">Find matches</p>
<ol class="flow">
<li class="step"><label for="f-who">I am a</label>
<select id="f-who" name="who">
<option value="">Anyone</option>
<option value="landlord">Landlord</option>
<option value="sole">Self-employed</option>
<option value="both">Both</option>
</select></li>
<li class="arrow" aria-hidden="true">→</li>
<li class="step"><label for="f-want">I want</label>
<select id="f-want" name="want">
<option value="">Any price</option>
<option value="free">Free</option>
<option value="low">Low cost</option>
<option value="full">Full bookkeeping</option>
</select></li>
<li class="arrow" aria-hidden="true">→</li>
<li class="step"><label for="f-keep">I keep records in</label>
<select id="f-keep" name="keep">
<option value="">Any method</option>
<option value="spreadsheet">Spreadsheet</option>
<option value="app">App</option>
<option value="paper">Paper</option>
</select></li>
<li class="go"><button type="submit" class="btn big">Show my matches</button></li>
</ol>
<noscript><p class="disclose">To shortlist products, use the filters in the full list below.</p></noscript>
</form>
<div id="matches" class="matches" hidden>
<h2 class="matches-h">Matches what you picked</h2>
<p class="matches-note"></p>
<div class="pcards"></div>
<p class="matches-more"><a href="#directory">Compare all {n} products</a></p>
</div>
<script type="application/json" id="finder-data">{finder_payload()}</script>
<p class="date-strip"><strong>MTD start dates:</strong> <span>6 Apr 2026 · over £50,000</span> <span>6 Apr 2027 · over £30,000</span> <span>6 Apr 2028 · over £20,000</span> <a href="/do-i-need-mtd/">See the start dates explained</a></p>
</div></section>
<div class="wrap">
<section id="directory"><h2>Compare all HMRC-recognised MTD software</h2>
<p class="disclose commercial"><strong>How this list is ordered:</strong> our featured products are ones whose providers run an affiliate programme we can join, so we may earn a commission if you sign up. That's why they're shown first: the featured section is commercial, not a purely editorial ranking. {'Affiliate links are marked next to the button. ' if any_aff else "Right now none of our links are affiliate links; every button goes to the provider's official website. "}Within each group, paid plans are listed before free variants, then A to Z; that is not a commission ranking. Every HMRC-recognised product is still listed below, and the facts for every product are checked the same way. <a href="/affiliate-disclosure/">How we make money</a>.</p>
<section class="featured" aria-labelledby="featured-h"><h3 id="featured-h">Featured MTD software</h3>
<p class="featured-note">{len(FEATURED)} HMRC-recognised products we may earn a commission from. Paid plans are listed before free variants, then A to Z. Prices checked on each provider's own website.</p>
<div class="pcards fcards">{''.join(featured_card(p) for p in FEATURED)}</div></section>
<h3 id="rest-h" class="rest-h">Best of the rest</h3>
<p class="rest-note">The other {n - len(FEATURED)} HMRC-recognised products, in the full table below with the featured products at the top. Filter, sort or search the whole list.</p>
<form class="filters" role="search" onsubmit="return false">
<input type="search" id="q" placeholder="Search by name, e.g. Xero" aria-label="Search software by name">
<label><input type="checkbox" data-f="free"> Free version</label>
<label><input type="checkbox" data-f="bridging"> Bridging (spreadsheets)</label>
<label><input type="checkbox" data-f="uk_property"> Landlord (UK property)</label>
<label><input type="checkbox" data-f="sole_trader"> Sole trader</label>
<label><input type="checkbox" data-f="foreign_property"> Foreign property</label>
<label><input type="checkbox" data-f="cis"> CIS ready</label>
<label><input type="checkbox" data-f="tax_return"> Files tax return too</label>
<label><input type="checkbox" data-f="joint"> Joint property (confirmed)</label>
<label><input type="checkbox" data-f="calendar"> Calendar update periods</label>
<label><input type="checkbox" data-f="checked"> Price-checked only</label>
<label class="pcf"><input type="checkbox" id="pcf" checked> Show price-checked first</label>
<select id="aud" aria-label="Who will use it"><option value="">For anyone</option><option value="i">For individuals</option><option value="a">For agents/accountants</option></select>
</form>
<p class="count" id="count" aria-live="polite">{n} HMRC-recognised products. Featured products first, then Best of the rest; price-checked first, paid plans before free variants, then A to Z within each.</p>
<p class="legend"><span class="u" aria-hidden="true">–</span> means we haven't checked it yet, or HMRC doesn't list it. Hover or tap a dash for details.</p>
<div class="tablewrap"><table class="dir" id="dir"><thead><tr>
<th data-k="name"><button>Software</button></th><th data-k="price"><button>Price (from)</button></th><th data-k="free"><button>Free version</button></th>
<th>Type</th><th>Income sources</th><th>Submits</th><th data-k="cis"><button>CIS on tax return</button></th><th data-k="joint"><button>Joint property</button></th>
</tr></thead><tbody class="g-featured"><tr class="grp" data-grp="featured"><th colspan="8" scope="colgroup">Featured ({len(rows[True])})</th></tr>{''.join(rows[True])}</tbody>
<tbody class="g-rest"><tr class="grp" data-grp="rest"><th colspan="8" scope="colgroup">Best of the rest ({len(rows[False])})</th></tr>{''.join(rows[False])}</tbody></table></div>
<p class="disclose">Free version, type, income sources, what it submits and CIS come from <a href="{FINDER}">HMRC's software finder</a> (read {nice_date(HMRC_DATE)}). "CIS on tax return" means HMRC lists the product as ready to report Construction Industry Scheme deductions on your tax return. Prices and joint-property support come from each provider's own website (checked {nice_date(CHECKED)}, or the later date shown on a product's page). <a href="/methodology/">How we check</a>.</p>
</section>
<details><summary>Free options we have price-checked</summary>
<p>These are free, or have a free plan, according to the provider's own website. Free plans usually have limits, so read the note before you choose.</p>
<ul>{free_list}</ul><p><a href="/guides/free-mtd-software/">Learn more: what each free plan includes, and the catches →</a></p>
</details>
<section><h2>Common questions</h2>{faq_html(qas)}</section>
<p class="below-fold-cta"><a href="/founders-blog/">Founders Blog</a>, by {E(OPERATOR)}. <a href="/methodology/">How we check</a>.</p>
</div>
{signup_block('home')}
<script src="/assets/directory.js" defer></script>
<script src="/assets/funnel.js" defer></script>'''
    out += foot()
    write('/', out)

# ---------- product pages ----------
def seo_label(name):
    """Title-safe form of a product name, avoiding repeated words in the name itself."""
    if not repeated_words(name):
        return name
    trimmed = re.sub(r'\s+[–-]\s+Making Tax Digital for Income Tax\s*$', '', name, flags=re.I)
    trimmed = re.sub(r'\s+for Income Tax\s*$', '', trimmed, flags=re.I)
    if trimmed and not repeated_words(trimmed):
        return trimmed
    m = re.match(r'^(\d+)\s+(\d+)(\b.*)$', name)
    if m and m.group(1) == m.group(2):
        alt = f"{m.group(1)}-{m.group(2)}{m.group(3)}"
        if not repeated_words(alt):
            return alt
    return name

def product_seo_title(p, heading):
    """Unique, repeat-free product title; keywords (the name) first, 55-65 chars when possible."""
    label = seo_label(heading)
    if is_free_variant(p):
        stems = [
            f"{label} price, limits & features",
            f"{label}: price, limits and features",
            f"{label}: prices and key features",
            f"{label}: price and features compared",
            f"{label}: Making Tax Digital limits & features",
            f"{label}: Making Tax Digital prices and features",
            f"{label}: Making Tax Digital prices and features compared",
            f"{label} prices, plans and features compared",
            f"{label}: HMRC-recognised prices and features",
            f"{label} on the HMRC list: price and features",
        ]
    elif pair_counterpart(p):
        stems = [
            f"{label} price, plan & features",
            f"{label}: prices and key features",
            f"{label}: price and features compared",
            f"{label} paid plan: prices and features",
            f"{label}: price, plan and features",
            f"{label}: Making Tax Digital price & features",
            f"{label}: Making Tax Digital prices and features",
            f"{label}: Making Tax Digital prices and features compared",
            f"{label} prices, plans and features compared",
            f"{label}: HMRC-recognised prices and features",
        ]
    elif 'free' in title_words(label):
        stems = [
            f"{label} price & features",
            f"{label}: prices and key features",
            f"{label}: price and features compared",
            f"{label}: Making Tax Digital price & features",
            f"{label}: Making Tax Digital prices and features compared",
            f"{label} prices, plans and features compared",
            f"{label}: HMRC-recognised prices and features",
        ]
    else:
        stems = [
            f"{label} price, free plan & features",
            f"{label}: price, free plan and features",
            f"{label}: prices and key features",
            f"{label}: price and features compared",
            f"{label}: price, limits and features",
            f"{label} price, limits & features",
            f"{label}: Making Tax Digital price & features",
            f"{label}: Making Tax Digital prices and features",
            f"{label}: Making Tax Digital prices and features compared",
            f"{label} prices, plans and features compared",
            f"{label} paid plan: prices and features",
            f"{label}: HMRC-recognised prices and features",
            f"{label} on the HMRC list: price and features",
        ]
    pads = ['', ' compared', ' today', ' in the UK', ' at a glance', ' for UK users']
    cands = []
    for stem in stems:
        for pad in pads:
            if pad and stem.endswith(pad.strip()):
                continue
            body = stem + pad
            cands.append(body)
            cands.append(f"{body} | {NAME}")
    cands += [f"{label} | {NAME}", label]
    return choose_title(cands)


def product_page(p):
    href, rel, aff = link_for(p)
    inc = incomes(p)
    tr = p['tax_return_items']
    ready = [k for k, v in tr.items() if v == 'yes']; dev = [k for k, v in tr.items() if v == 'in development']; no = [k for k, v in tr.items() if v == 'no']
    tlist = ' and '.join(x.lower() for x in ['software that creates digital records' if p['creates_records'] == 'yes' else '', 'bridging software that connects to your records' if p['bridging'] == 'yes' else ''] if x) or 'software'
    other = pair_counterpart(p)
    heading = p['name']
    if is_free_variant(p) and not re.search(r'\bfree\b', heading, re.I):
        heading = f"{heading} Free"
    inc_txt = ', '.join(inc).replace('Sole trader', 'sole trader').replace('Foreign property', 'foreign property') or 'unknown'
    if is_free_variant(p) and other:
        summary = f"{E(heading)} is the free version of {E(other['name'])}, listed separately on HMRC's list of software recognised for Making Tax Digital for Income Tax. HMRC lists it as {tlist}, for {inc_txt} income. "
    elif other:
        summary = f"{E(p['name'])} is on HMRC's list of software recognised for Making Tax Digital for Income Tax. This page is about the paid product, not the free version. HMRC lists it as {tlist}, for {inc_txt} income. "
    else:
        summary = f"{E(p['name'])} is on HMRC's list of software recognised for Making Tax Digital for Income Tax. HMRC lists it as {tlist}, for {inc_txt} income. "
    summary += 'It can send your quarterly updates <strong>and submit your tax return</strong>.' if p['tax_return'] else 'HMRC lists it for <strong>quarterly updates only</strong>, so you would need another product or an agent for your tax return.'
    suits = []
    if inc == ['UK property'] or inc == ['UK property', 'Foreign property']: suits.append('It is built for landlords: HMRC lists property as its only income type.')
    if inc == ['Sole trader']: suits.append('It covers self-employment only, so it will not handle rental income.')
    if p['bridging'] == 'yes': suits.append('It can work with records you already keep, such as a spreadsheet.')
    if p['free_version'] == 'yes': suits.append('HMRC says there is a free version. Check its limits on the provider site.')
    if p['agent'] == 'yes' and p['individual'] != 'yes': suits.append('HMRC lists it as agent software, aimed at accountants and bookkeepers rather than individuals.')
    if p['cis'] == 'yes': suits.append('It is ready to report Construction Industry Scheme (CIS) deductions on your tax return.')
    # Free variants always keep "Free" in the heading used for the title and H1.
    title = product_seo_title(p, heading)
    checked = (', checked ' + nice_date(p['price_checked'])) if p['vendor_checked'] else ''
    if is_free_variant(p):
        desc = f"Is {heading} HMRC-recognised for MTD? Yes. This page is about the free version: price{checked}, limits and key features in plain English."
    elif other:
        desc = f"Is {p['name']} HMRC-recognised for MTD? Yes. This page is about the paid product: price{checked} and key features in plain English."
    else:
        desc = f"Is {p['name']} HMRC-recognised for MTD? Yes. See price{checked}, free version and key features in plain English."
    desc = fit_desc(desc)
    app = {'@context': 'https://schema.org', '@type': 'SoftwareApplication', 'name': p['name'], 'applicationCategory': 'FinanceApplication',
           'operatingSystem': p['compatible_with'] if p['compatible_with'] != 'unknown' else None, 'url': p['website'],
           'description': re.sub('<[^>]+>', '', summary)}
    if p['price_from_gbp_month'] is not None or p['price_from_gbp_year'] is not None:
        if p['price_from_gbp_month'] is not None:
            price, unit = p['price_from_gbp_month'], 'MON'
        else:
            price, unit = p['price_from_gbp_year'], 'ANN'
        app['offers'] = {'@type': 'Offer', 'price': f'{price:.2f}', 'priceCurrency': 'GBP', 'url': p['price_source'],
                         'description': p['price_text'], 'priceSpecification': {'@type': 'UnitPriceSpecification', 'price': f'{price:.2f}', 'priceCurrency': 'GBP', 'unitCode': unit} if price else None}
        if not price: app['offers'].pop('priceSpecification')
    app = {k: v for k, v in app.items() if v is not None}
    crumbs = [('Home', '/'), ('MTD software', '/#directory'), (p['name'], f"/software/{p['slug']}/")]
    out = head(title, desc, f"/software/{p['slug']}/", [app, crumb_ld(crumbs)], noindex=p['slug'] not in INDEXABLE)
    cta = outbound_cta(p, kind='product', page='product', label=f"Visit {p['name']}")
    cta_note = '<span class="disclose">Affiliate link: we may earn a commission if you sign up. <a href="/affiliate-disclosure/">Disclosure</a>.</span>' if aff else '<span class="disclose">Official website, as listed by HMRC. <a href="/affiliate-disclosure/">How we make money</a>.</span>'
    price_block = (f'<p><strong>{E(p["price_text"])}</strong></p>' + (f'<p>{E(p["price_note"])}</p>' if p.get('price_note') else '') +
                   f'<p class="disclose">Checked {nice_date(p["price_checked"])} on <a href="{E(p["price_source"])}" rel="noopener" target="_blank">the provider\'s pricing page</a>. Prices and offers change, so confirm before you buy.</p>') if p['price_text'] != 'unknown' or p.get('price_note') else \
        f'<p>We haven\'t checked this price yet. HMRC says: <strong>{"free version available" if p["free_version"] == "yes" else "paid version"}</strong>. See the provider\'s website for current pricing.</p>'
    joint = yn(p['joint_property']) + (f' <a class="disclose" href="{E(p["joint_source"])}" rel="noopener" target="_blank">(source)</a>' if p.get('joint_source') else '')
    alts = [a for a in CHECKEDP if a['slug'] != p['slug'] and set(incomes(a)) & set(inc)]
    alts.sort(key=lambda a: (not a['featured'], is_free_variant(a), a['sort_price'] if a['sort_price'] is not None else 999, a['name']))
    alt_html = ''.join(f'<li><a href="/software/{a["slug"]}/">{E(a["name"])}</a>{" <span class=\"tag f\">Featured</span>" if a["featured"] else ""}: {card_price(a)}</li>' for a in alts[:5])
    tr_rows = ''.join(f'<tr><td>{E(k)}</td><td>{yn(v)}</td></tr>' for k, v in tr.items())
    acc = ', '.join(k for k, v in p['accessibility'].items() if v == 'yes') or 'None listed'
    filing = " It can send quarterly updates and submit your tax return." if p['tax_return'] else " HMRC lists it for quarterly updates only."
    if is_free_variant(p) and other:
        short = f"{E(heading)} is the free version of {E(other['name'])}, listed separately by HMRC for Making Tax Digital for Income Tax.{filing}"
        if p.get('price_note'):
            short += f" {E(p['price_note'].rstrip('.'))}."
        elif p['price_text'] and p['price_text'] != 'unknown':
            short += f" {E(p['price_text'])}."
        else:
            short += " We have not yet checked this free plan on the provider's website."
        pair_nav = f'<p class="disclose pair-nav">Looking for the paid version? See <a href="/software/{other["slug"]}/">{E(other["name"])}</a>.</p>'
    elif other:
        short = f"{E(p['name'])} is HMRC-recognised for Making Tax Digital for Income Tax.{filing} This page is about the paid product, not the free version."
        pair_nav = f'<p class="disclose pair-nav">Looking for the free version? See <a href="/software/{other["slug"]}/">{E(other["name"])}</a>.</p>'
    else:
        short = f"{E(p['name'])} is HMRC-recognised for Making Tax Digital for Income Tax.{filing}"
        pair_nav = ''
    out += f'''<div class="wrap"><p class="breadcrumb"><a href="/">Home</a> › <a href="/#directory">MTD software</a> › {E(p['name'])}</p>
<div class="cols"><div>
<h1>{E(heading)}</h1>
<p class="lead">{short}</p>
{pair_nav}<div class="cta">{cta}{cta_note}</div>
<div class="facts">
<div class="fact"><small>On HMRC's list</small><b class="y">Yes</b> <a class="disclose" href="{E(p['hmrc_url'])}" rel="noopener" target="_blank">(HMRC entry)</a></div>
<div class="fact"><small>Free version (HMRC)</small><b>{yn(p['free_version'])}</b></div>
<div class="fact"><small>Bridging / spreadsheets</small><b>{yn(p['bridging'])}</b> <a class="disclose" href="/guides/mtd-spreadsheets-bridging-software/">(bridging guide)</a></div>
<div class="fact"><small>Landlords (UK property)</small><b>{yn(p['uk_property'])}</b></div>
<div class="fact"><small>Sole traders</small><b>{yn(p['sole_trader'])}</b></div>
<div class="fact"><small>Foreign property</small><b>{yn(p['foreign_property'])}</b> <a class="disclose" href="/guides/mtd-foreign-property/">(foreign property guide)</a></div>
<div class="fact"><small>CIS on tax return</small><b>{yn(p['cis'])}</b></div>
<div class="fact"><small>Joint property splits</small><b>{joint}</b> <a class="disclose" href="/guides/jointly-owned-property-mtd/">(joint property guide)</a></div>
<div class="fact"><small>Submits</small><b>{E(p['submits'])}</b></div>
<div class="fact"><small>MTD for VAT too</small><b>{yn(p['vat'])}</b></div>
<div class="fact"><small>HMRC Assist built in</small><b>{yn(p['hmrc_assist'])}</b></div>
<div class="fact"><small>Runs on</small><b>{E(p['software_type'])}</b><br><small>{E(p['compatible_with'])}</small></div>
</div>
<h2>Price</h2>{price_block}{('<p class="disclose">HMRC lists a free version of this product. See <a href="/guides/free-mtd-software/">free MTD software: what is really free, and the catches</a>.</p>') if p['free_version'] == 'yes' else ''}
<h2>What it can put on your tax return</h2>
<p>HMRC lists {len(ready)} of {len(tr)} other income and tax-return items as ready now{f", {len(dev)} in development" if dev else ""}{f" and {len(no)} not included" if no else ""}. "In development" means the provider has told HMRC it will build it in time for the 2026 to 2027 tax return.</p>
<div class="tablewrap"><table><thead><tr><th>Item</th><th>Status (HMRC)</th></tr></thead><tbody>{tr_rows}</tbody></table></div>
<h2>Other details</h2>
<p>Update periods: standard (6 April to 5 April) {yn(p['standard_period'])}; calendar (1 April to 31 March) {yn(p['calendar_period'])} (<a href="/guides/mtd-standard-vs-calendar-update-periods/">what's the difference?</a>). For individuals: {yn(p['individual'])}. For agents: {yn(p['agent'])}. Accessibility features listed: {E(acc)}. Language: {E(p['language'])}.</p>
<h2>Getting started</h2>
<ol><li>Check you need MTD and when: <a href="/do-i-need-mtd/">our plain-English guide</a>.</li>
<li><a href="https://www.gov.uk/guidance/sign-up-for-making-tax-digital-for-income-tax" rel="noopener">Sign up for Making Tax Digital for Income Tax</a> on GOV.UK, if you haven't already.</li>
<li>Choose your software, then <a href="https://www.gov.uk/guidance/use-making-tax-digital-for-income-tax/get-your-software-ready" rel="noopener">authorise it with HMRC</a>.</li></ol>
{signup_block('inline')}
</div>
<aside><div class="card"><strong>{E(p['name'])}</strong><p>{price_html(p)}</p>{cta}<p>{cta_note}</p>
{('<h3>Price-checked alternatives</h3><ul>' + alt_html + '</ul><p class="disclose">Featured products are listed first, then paid plans before free variants; <a href="/affiliate-disclosure/">we may earn a commission</a> from featured products.</p>') if alt_html else ''}
<p><a href="/#directory">← Compare all {len(products)} products</a></p></div></aside>
</div></div>'''
    out += foot()
    write(f"/software/{p['slug']}/", out)

# ---------- guide ----------
def guide():
    G = 'https://www.gov.uk/guidance/'
    qas = [
        ("Do I need to use Making Tax Digital for Income Tax?", "You need to use it if you're a sole trader or landlord registered for Self Assessment, you get income from self-employment or property (or both), and your qualifying income is over the threshold for the relevant tax year."),
        ("What are the Making Tax Digital thresholds?", "Over £50,000 of qualifying income in the 2024 to 2025 tax year means you start from 6 April 2026. Over £30,000 in 2025 to 2026 means from 6 April 2027. Over £20,000 in 2026 to 2027 means from 6 April 2028."),
        ("Does my salary count towards the MTD threshold?", "No. Qualifying income is your self-employment and property income before expenses. Employment (PAYE) income, a share of partnership profit, dividends and pensions do not count."),
        ("Does rent from a property abroad count towards the MTD threshold?", "If you were UK tax resident, yes: GOV.UK counts UK and foreign property income, before expenses, alongside self-employment income. If you weren't UK tax resident, foreign property income doesn't count. Under MTD your overseas lettings form one foreign property business with its own quarterly updates. See <a href=\"/guides/mtd-foreign-property/\">MTD and foreign property</a>."),
        ("What if my qualifying income is £20,000 or less?", "HMRC says you are automatically exempt and do not need to use Making Tax Digital for Income Tax. You still send a Self Assessment tax return as normal."),
        ("Can I apply for an exemption from MTD if I can't use a computer?", "GOV.UK says you can apply if you're digitally excluded: for example your age, health condition or disability stops you using a computer, tablet or smartphone, or you can't get internet access because of your location. Being unfamiliar with software, having few records, or the extra time or cost isn't enough on its own. You apply by phone or letter. See <a href=\"/guides/mtd-exemption-digitally-excluded/\">how MTD exemptions and digital exclusion work</a>."),
        ("Should I use standard or calendar update periods?", "GOV.UK says standard update periods (ending on the 5th) are the default and fit accounts that follow the tax year, and calendar update periods (ending on the month-end) are for accounts that run 1 April to 31 March. The deadlines are the same for both, and the choice is fixed for the tax year once you send your first update. See <a href=\"/guides/mtd-standard-vs-calendar-update-periods/\">standard vs calendar update periods</a>."),
        ("Will I get a penalty for a late quarterly update in 2026 to 2027?", "HMRC says there are no penalty points for late quarterly updates in your first tax year if you need to use MTD from 6 April 2026 or 6 April 2027 (so 2026 to 2027, or 2027 to 2028). You still need to send them before you can submit your tax return, and late tax returns still get penalty points. See <a href=\"/guides/mtd-late-quarterly-update-penalties/\">how MTD penalty points work</a>."),
    ]
    out = head(choose_title([
        f'Do I need Making Tax Digital yet? | {NAME}',
        'Do I need Making Tax Digital, and when?',
        'Do I need Making Tax Digital yet?',
    ]),
               'Who needs MTD for Income Tax, the £50,000, £30,000 and £20,000 thresholds, quarterly deadlines and exemptions. Sourced from GOV.UK.',
               '/do-i-need-mtd/', [faq_ld(qas), crumb_ld([('Home', '/'), ('Do I need MTD?', '/do-i-need-mtd/')])])
    out += f'''<div class="wrap" style="max-width:820px"><p class="breadcrumb"><a href="/">Home</a> › Do I need MTD?</p>
<h1>Do I need Making Tax Digital, and when?</h1>
<p class="lead">If you're a sole trader or landlord and your self-employment plus property income <em>before expenses</em> is over £50,000, you should already be using it. Over £30,000, April 2027. Over £20,000, April 2028.</p>
<p class="cta"><a class="btn" href="/#finder">See matching software</a> <a class="btn ghost" href="/#directory">Compare all {len(products)} products</a></p>
<p class="disclose">Every fact on this page comes from GOV.UK and is linked. Last checked {nice_date(CHECKED)}. <a href="/methodology/">How we check</a>.</p>
<h2>Who needs to use it</h2>
<p>According to HMRC, you need to use Making Tax Digital for Income Tax if <strong>all</strong> of these apply:</p>
<ul><li>you're a sole trader or a landlord registered for Self Assessment</li><li>you get income from self-employment or property, or both</li><li>your qualifying income is over the threshold for the relevant tax year</li></ul>
<p class="disclose">Source: <a href="{ELIGIBILITY_URL}">GOV.UK, Find out if and when you need to use Making Tax Digital for Income Tax</a>.</p>
<h2>When you need to start</h2>
<div class="tablewrap"><table><thead><tr><th>If your qualifying income was over…</th><th>…in the tax year</th><th>You need to use MTD from</th></tr></thead><tbody>
<tr><td>£50,000</td><td>2024 to 2025</td><td>6 April 2026 (now live)</td></tr>
<tr><td>£30,000</td><td>2025 to 2026</td><td>6 April 2027</td></tr>
<tr><td>£20,000</td><td>2026 to 2027</td><td>6 April 2028</td></tr></tbody></table></div>
<p>HMRC checks your Self Assessment tax return each year. If you're over the threshold it will write to you, but HMRC is clear that if you don't get a letter it is still your responsibility to check. Partnerships will need to join later; HMRC hasn't set the date yet.</p>
<p>Starting in April 2027? See <a href="/guides/sign-up-mtd-april-2027/">how and when to sign up if you're over £30,000</a>, including whether HMRC signs you up and the key dates for your first year.</p>
<p class="disclose">Source: <a href="{ELIGIBILITY_URL}">GOV.UK</a>. You can also use <a href="https://tax.service.gov.uk/guidance/check-if-you-need-to-use-making-tax-digital-for-income-tax">HMRC's own checker tool</a>.</p>
<h2>What counts as qualifying income</h2>
<p>Qualifying income is your <strong>total income from self-employment and property, before expenses</strong> (your turnover), based on the tax return for the earlier tax year. HMRC's own example: £25,000 of rental income plus £27,000 of self-employment income gives qualifying income of £52,000.</p>
<p><strong>It does not include</strong> employment (PAYE) income, your share of profit from a partnership as an individual partner, dividends (including from your own company), the State Pension or private pensions.</p>
<p>If you were UK tax resident, rent from property abroad counts too; if you weren't, only UK property income and self-employment income on your UK return count. See <a href="/guides/mtd-foreign-property/">MTD and foreign property</a>.</p>
<p class="disclose">Source: <a href="{G}work-out-your-qualifying-income-for-making-tax-digital-for-income-tax">GOV.UK, Work out your qualifying income</a>.</p>
<h2>What you'll have to do</h2>
<ol><li><strong>Keep digital records</strong> of your self-employment and property income and expenses in compatible software.</li>
<li><strong>Send quarterly updates</strong> every 3 months. These are summaries, not tax returns. Each one covers the tax year so far.</li>
<li><strong>Submit your tax return</strong> through software by 31 January after the tax year, adding any other income.</li></ol>
<p class="disclose">Source: <a href="{G}choose-the-right-software-for-making-tax-digital-for-income-tax">GOV.UK, Choose the right software</a>.</p>
<h2>Quarterly update deadlines</h2>
<div class="tablewrap"><table><thead><tr><th>Standard period (tax year)</th><th>Calendar period</th><th>Deadline</th></tr></thead><tbody>
<tr><td>6 April to 5 July</td><td>1 April to 30 June</td><td>7 August</td></tr>
<tr><td>6 April to 5 October</td><td>1 April to 30 September</td><td>7 November</td></tr>
<tr><td>6 April to 5 January</td><td>1 April to 31 December</td><td>7 February</td></tr>
<tr><td>6 April to 5 April</td><td>1 April to 31 March</td><td>7 May (following tax year)</td></tr></tbody></table></div>
<p>If you've had no income or expenses in a period, you still have to send the update. If you want calendar periods, choose that in your software before you send your first update, because you can't change it for the rest of the tax year afterwards. More on <a href="/guides/mtd-standard-vs-calendar-update-periods/">standard vs calendar update periods</a>, including which software lists calendar periods.</p>
<p class="disclose">Source: <a href="{G}use-making-tax-digital-for-income-tax/send-quarterly-updates">GOV.UK, Send quarterly updates</a>.</p>
{signup_block('inline')}
<h2>Penalties</h2>
<p>Late quarterly updates and late tax returns earn penalty points. At 4 points there's a £200 penalty, and another £200 for each further missed deadline. If you need to use MTD from 6 April 2026 or 6 April 2027, HMRC says there are <strong>no penalty points for late quarterly updates in your first tax year</strong>. You still need to send them before you can submit your tax return, and late tax returns still get points.</p>
<p>Read <a href="/guides/mtd-late-quarterly-update-penalties/">how MTD penalty points, late payment penalties and appeals work</a>, with worked timelines.</p>
<p class="disclose">Sources: <a href="{G}penalties-for-making-tax-digital-for-income-tax">GOV.UK, Penalties for Making Tax Digital for Income Tax</a>; <a href="{G}use-making-tax-digital-for-income-tax/send-quarterly-updates">GOV.UK, Send quarterly updates</a>.</p>
<h2>If you own property jointly</h2>
<p>For jointly let property, HMRC lets you include either income and expenses, or income only, in your quarterly updates. If you leave out expenses, you report them after the tax year by resending your fourth quarterly update before you submit your tax return. Properties you own alone still need both income and expenses in every update.</p>
<p class="disclose">Source: <a href="{G}use-making-tax-digital-for-income-tax/send-quarterly-updates">GOV.UK, Send quarterly updates</a>. See which software confirms joint-property support with the <a href="/?f=joint#directory">joint property filter</a>, or read our <a href="/guides/jointly-owned-property-mtd/">full guide to jointly owned property under MTD</a>.</p>
<h2>Who is exempt</h2>
<ul><li><strong>Qualifying income of £20,000 or less:</strong> automatically exempt.</li>
<li><strong>No National Insurance number</strong> before the start of the tax year: automatically exempt.</li>
<li><strong>Partnerships:</strong> don't currently need to use it.</li>
<li>Some people, for example those who are <strong>digitally excluded</strong>, can apply for an exemption.</li></ul>
<p>If you're exempt you still send a Self Assessment tax return as normal. Read <a href="/guides/mtd-exemption-digitally-excluded/">who is automatically exempt, and how to apply if you're digitally excluded</a>, including what HMRC won't accept and how appeals work.</p>
<p class="disclose">Source: <a href="{G}find-out-if-you-can-get-an-exemption-from-making-tax-digital-for-income-tax">GOV.UK, Find out if you can get an exemption</a>.</p>
<h2>Next step: pick your software</h2>
<p>You'll need HMRC-recognised software. <a class="btn" href="/#directory">Compare all {len(products)} products</a></p>
<p>Browse our <a href="/guides/">plain-English MTD guides</a>, including <a href="/guides/free-mtd-software/">which free MTD software options exist and their limits</a>, <a href="/guides/mtd-spreadsheets-bridging-software/">whether you can keep using spreadsheets</a>, <a href="/guides/mtd-late-quarterly-update-penalties/">how late-update penalty points work</a>, <a href="/guides/mtd-exemption-digitally-excluded/">MTD exemptions and digital exclusion</a>, <a href="/guides/mtd-foreign-property/">MTD for foreign property</a> and <a href="/guides/mtd-standard-vs-calendar-update-periods/">standard vs calendar update periods</a>.</p>
<h2>Quick answers</h2>{faq_html(qas)}
</div>'''
    out += foot()
    write('/do-i-need-mtd/', out)

def simple(path, title, desc, body, crumbs):
    out = head(choose_title([f'{title} | {NAME}', title]), desc, path, [crumb_ld(crumbs)])
    out += f'<div class="wrap" style="max-width:820px"><p class="breadcrumb"><a href="/">Home</a> › {E(title)}</p><h1>{E(title)}</h1>{body}</div>'
    out += foot(); write(path, out)


# ---------- Guides (data/guides/*.html: <!--meta {json} --> + HTML body with {{tokens}}) ----------
def _tr(p):
    return '<span class="y">Yes</span>' if p['tax_return'] else '<span class="n">Not listed</span>'

def _inc(p):
    return E(', '.join(incomes(p)) or 'Unknown')

def _ptype(p):
    return E(' + '.join(types(p)) or 'Unknown')

def _plink(p):
    href, rel, aff = link_for(p)
    tag = ' <small class="disclose">(affiliate link)</small>' if aff else ''
    return f'<a href="{E(href)}" rel="{rel}" target="_blank">Provider site</a>{tag}'

FREE = [p for p in products if p['free_version'] == 'yes']
FREE_CHECKED = [p for p in FREE if p['vendor_checked'] and p['price_text'] != 'unknown' and 'per HMRC' not in p['price_text']]
FREE_UNCHECKED = [p for p in FREE if p not in FREE_CHECKED]

def _ulink(href, rel, text, target='_blank'):
    tgt = ' target="_blank"' if target == '_blank' else ''
    return f'<a class="unverified-link" href="{E(href)}" rel="{E(rel)}"{tgt}>{text}</a>'

def _uplink(p):
    href, rel, aff = link_for(p)
    tag = ' <small class="disclose">(affiliate link)</small>' if aff else ''
    site = _ulink(href, rel, 'Provider site')
    hmrc = _ulink(p['hmrc_url'], 'noopener', 'HMRC listing') if p.get('hmrc_url') else ''
    return site + tag + (f' · {hmrc}' if hmrc else '')

UNVERIFIED_DIALOG = """
<dialog id="unverified-dialog" class="unverified-dialog" aria-labelledby="unverified-dialog-title" aria-describedby="unverified-dialog-desc">
<h2 id="unverified-dialog-title">We haven't verified this one yet</h2>
<p id="unverified-dialog-desc">This product is listed as having a free version in HMRC's software finder. We haven't yet checked the free plan on the provider's own website, so please confirm the details there.</p>
<div class="dialog-actions">
<button type="button" class="btn ghost" data-unverified-close>Close</button>
<a class="btn" data-unverified-continue href="#">Continue to the link</a>
</div>
</dialog>
"""

def tok_free_checked_table():
    return tok_free_plans_table()

def tok_free_unchecked_table():
    return ''

def tok_free_plans_table():
    head = ('<div class="tablewrap"><table class="free-plans"><thead><tr><th>Software</th><th>Free plan (provider)</th><th>What the provider says about it</th>'
            '<th>Income types (HMRC)</th><th>Tax return (HMRC listing)</th><th>Type</th><th>Links</th></tr></thead>')
    checked = ''.join(
        f'<tr><td><a href="/software/{p["slug"]}/">{E(p["name"])}</a></td><td>{E(p["price_text"])}</td><td>{E(p["price_note"] or "Not stated")}</td>'
        f'<td>{_inc(p)}</td><td>{_tr(p)}</td><td>{_ptype(p)}</td><td>{_plink(p)} · <a href="{E(p["price_source"])}" rel="noopener" target="_blank">price source</a></td></tr>'
        for p in FREE_CHECKED)
    unchecked = ''.join(
        f'<tr class="unverified"><td>{_ulink("/software/" + p["slug"] + "/", "noopener", E(p["name"]), target=None)}</td>'
        f'<td>Not yet checked</td><td>Unknown</td><td>{_inc(p)}</td><td>{_tr(p)}</td><td>{_ptype(p)}</td><td>{_uplink(p)}</td></tr>'
        for p in FREE_UNCHECKED)
    label = ''
    if FREE_UNCHECKED:
        label = (f'<tr class="unverified-label"><th scope="col" colspan="7">Other free versions on HMRC\'s list '
                 f'({len(FREE_UNCHECKED)}, not yet checked by us). Limits are unknown here.</th></tr>')
    return (head + f'<tbody>{checked}</tbody><tbody>{label}{unchecked}</tbody></table></div>' + UNVERIFIED_DIALOG)

def tok_joint_table():
    rows = ''.join(
        f'<tr><td><a href="/software/{p["slug"]}/">{E(p["name"])}</a></td>'
        f'<td>{"Paid plans only" if p["joint_property"] == "paid plans only" else "Yes"}</td>'
        f'<td><a href="{E(p["joint_source"])}" rel="noopener" target="_blank">Provider page</a></td></tr>'
        for p in products if p['joint_property'] in ('yes', 'paid plans only') and p.get('joint_source'))
    return ('<div class="tablewrap"><table><thead><tr><th>Software</th><th>Joint-ownership splits (provider says)</th><th>Source</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div>')

BRIDGING = [p for p in products if p['bridging'] == 'yes']
BRIDGING_CHECKED = [p for p in BRIDGING if p['vendor_checked'] and p['price_text'] != 'unknown' and 'per HMRC' not in p['price_text']]

def tok_bridging_table():
    rows = ''.join(
        f'<tr><td><a href="/software/{p["slug"]}/">{E(p["name"])}</a></td><td>{E(p["price_text"])}</td><td>{E(p["price_note"] or "Not stated")}</td>'
        f'<td>{_inc(p)}</td><td>{_tr(p)}</td><td>{_plink(p)} · <a href="{E(p["price_source"])}" rel="noopener" target="_blank">price source</a></td></tr>'
        for p in BRIDGING_CHECKED)
    return ('<div class="tablewrap"><table><thead><tr><th>Software</th><th>Price (provider)</th><th>What the provider says</th>'
            '<th>Income types (HMRC)</th><th>Tax return (HMRC listing)</th><th>Links</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div>')

FP = [p for p in products if p['foreign_property'] == 'yes']
FP_CHECKED = [p for p in FP if p['vendor_checked'] and p['price_text'] != 'unknown' and 'per HMRC' not in p['price_text']]

def tok_fp_table():
    rows = ''.join(
        f'<tr><td><a href="/software/{p["slug"]}/">{E(p["name"])}</a></td><td>{E(p["price_text"])}</td><td>{E(p["price_note"] or "Not stated")}</td>'
        f'<td>{_inc(p)}</td><td>{_tr(p)}</td><td>{_ptype(p)}</td><td>{_plink(p)} · <a href="{E(p["price_source"])}" rel="noopener" target="_blank">price source</a></td></tr>'
        for p in FP_CHECKED)
    return ('<div class="tablewrap"><table><thead><tr><th>Software</th><th>Price (provider)</th><th>What the provider says about price</th>'
            '<th>Income types (HMRC)</th><th>Tax return (HMRC listing)</th><th>Type</th><th>Links</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div>')

def tok_fp_not_listed():
    ps = [p for p in products if p['vendor_checked'] and p['foreign_property'] != 'yes' and (p['uk_property'] == 'yes' or p['sole_trader'] == 'yes')]
    return ', '.join(f'<a href="/software/{p["slug"]}/">{E(p["name"])}</a>' for p in ps)

CAL = [p for p in products if p['calendar_period'] == 'yes']

def _listed(v):
    return '<span class="y">Yes</span>' if v == 'yes' else '<span class="n">Not listed</span>'

def tok_period_table():
    rows = ''.join(
        f'<tr><td><a href="/software/{p["slug"]}/">{E(p["name"])}</a></td><td>{E(p["price_text"])}</td>'
        f'<td>{_listed(p["standard_period"])}</td><td>{_listed(p["calendar_period"])}</td><td>{_inc(p)}</td><td>{_tr(p)}</td>'
        f'<td>{_plink(p)} · <a href="{E(p["price_source"])}" rel="noopener" target="_blank">price source</a></td></tr>'
        for p in products if p['vendor_checked'] and p['price_text'] != 'unknown' and 'per HMRC' not in p['price_text'])
    return ('<div class="tablewrap"><table><thead><tr><th>Software</th><th>Price (provider)</th><th>Standard periods (HMRC)</th>'
            '<th>Calendar periods (HMRC)</th><th>Income types (HMRC)</th><th>Tax return (HMRC listing)</th><th>Links</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div>')

def _cnt(f): return str(sum(1 for p in FREE if f(p)))
GUIDE_TOKENS = {
    'products_total': lambda: str(len(products)),
    'free_total': lambda: str(len(FREE)),
    'free_checked_n': lambda: str(len(FREE_CHECKED)),
    'free_unchecked_n': lambda: str(len(FREE_UNCHECKED)),
    'free_tr': lambda: _cnt(lambda p: p['tax_return']),
    'free_no_tr': lambda: _cnt(lambda p: not p['tax_return']),
    'free_both': lambda: _cnt(lambda p: p['sole_trader'] == 'yes' and p['uk_property'] == 'yes'),
    'free_both_tr': lambda: _cnt(lambda p: p['sole_trader'] == 'yes' and p['uk_property'] == 'yes' and p['tax_return']),
    'free_fp': lambda: _cnt(lambda p: p['foreign_property'] == 'yes'),
    'free_bridging': lambda: _cnt(lambda p: p['bridging'] == 'yes'),
    'free_cis': lambda: _cnt(lambda p: p['cis'] == 'yes'),
    'free_checked_table': tok_free_checked_table,
    'free_unchecked_table': tok_free_unchecked_table,
    'free_plans_table': tok_free_plans_table,
    'hmrc_date': lambda: nice_date(HMRC_DATE),
    'signup_inline': lambda: signup_block('inline'),
    'joint_table': tok_joint_table,
    'bridging_table': tok_bridging_table,
    'bridging_n': lambda: str(len(BRIDGING)),
    'bridging_tr': lambda: str(sum(1 for p in BRIDGING if p['tax_return'])),
    'bridging_no_tr': lambda: str(sum(1 for p in BRIDGING if not p['tax_return'])),
    'bridging_free': lambda: str(sum(1 for p in BRIDGING if p['free_version'] == 'yes')),
    'bridging_checked_n': lambda: str(len(BRIDGING_CHECKED)),
    'fp_n': lambda: str(len(FP)),
    'fp_tr': lambda: str(sum(1 for p in FP if p['tax_return'])),
    'fp_all3': lambda: str(sum(1 for p in FP if p['sole_trader'] == 'yes' and p['uk_property'] == 'yes')),
    'fp_all3_tr': lambda: str(sum(1 for p in FP if p['sole_trader'] == 'yes' and p['uk_property'] == 'yes' and p['tax_return'])),
    'fp_free': lambda: str(sum(1 for p in FP if p['free_version'] == 'yes')),
    'fp_bridging': lambda: str(sum(1 for p in FP if p['bridging'] == 'yes')),
    'uk_no_fp': lambda: str(sum(1 for p in products if p['uk_property'] == 'yes' and p['foreign_property'] != 'yes')),
    'uk_n': lambda: str(sum(1 for p in products if p['uk_property'] == 'yes')),
    'fp_checked_n': lambda: str(len(FP_CHECKED)),
    'fp_table': tok_fp_table,
    'fp_not_listed': tok_fp_not_listed,
    'cal_n': lambda: str(len(CAL)),
    'cal_no': lambda: str(len(products) - len(CAL)),
    'cal_tr': lambda: str(sum(1 for p in CAL if p['tax_return'])),
    'cal_free': lambda: str(sum(1 for p in CAL if p['free_version'] == 'yes')),
    'cal_bridging': lambda: str(sum(1 for p in CAL if p['bridging'] == 'yes')),
    'period_table': tok_period_table,
    'joint_n': lambda: str(sum(1 for p in products if p['joint_property'] in ('yes', 'paid plans only'))),
}

def load_guides():
    gs = []
    d = f'{ROOT}/data/guides'
    if not os.path.isdir(d): return gs
    for fn in sorted(os.listdir(d)):
        if not fn.endswith('.html'): continue
        raw = open(os.path.join(d, fn)).read()
        m = re.match(r'\s*<!--meta\s*(\{.*?\})\s*-->', raw, re.S)
        meta = json.loads(m.group(1)); body = raw[m.end():]
        def sub(mm, fn=fn):
            k = mm.group(1)
            if k not in GUIDE_TOKENS: raise KeyError(f'Unknown guide token {k} in {fn}')
            return GUIDE_TOKENS[k]()
        meta['html'] = re.sub(r'\{\{(\w+)\}\}', sub, body)
        meta['slug'] = fn[:-5]; meta['path'] = f'/guides/{meta["slug"]}/'
        meta['qas'] = [(q, re.sub(r'\{\{(\w+)\}\}', sub, a)) for q, a in meta.get('faqs', [])]
        gs.append(meta)
    gs.sort(key=lambda g: g['published'], reverse=True)
    return gs

GUIDES = load_guides()

def guide_pages():
    il = {'@context': 'https://schema.org', '@type': 'CollectionPage', 'name': f'Making Tax Digital guides · {NAME}', 'url': BASE + '/guides/',
          'inLanguage': 'en-GB', 'hasPart': [{'@type': 'Article', 'headline': g['title'], 'url': BASE + g['path']} for g in GUIDES]}
    items = '<li><p class="byline">Facts checked ' + E(nice_date(CHECKED)) + '</p><h2><a href="/do-i-need-mtd/">Do I need Making Tax Digital, and when?</a></h2><p>Who needs MTD for Income Tax, the thresholds, quarterly deadlines and exemptions, all sourced from GOV.UK.</p></li>'
    items += ''.join(f'''<li><p class="byline">Facts checked {E(nice_date(g["checked"]))}</p>
<h2><a href="{g["path"]}">{E(g["title"])}</a></h2><p>{E(g["description"])}</p></li>''' for g in GUIDES)
    out = head(choose_title([
        'Making Tax Digital guides for landlords and sole traders',
        f'Making Tax Digital guides | {NAME}',
    ]),
               "Plain-English guides to Making Tax Digital for Income Tax for landlords and sole traders, checked against GOV.UK and providers' own websites.",
               '/guides/', [il, crumb_ld([('Home', '/'), ('Guides', '/guides/')])])
    out += f'''<div class="wrap prose"><p class="breadcrumb"><a href="/">Home</a> › Guides</p><h1>Making Tax Digital guides</h1>
<p class="lead">Plain-English answers to the questions landlords and sole traders ask most about Making Tax Digital for Income Tax. Every fact is linked to its source.</p>
<ul class="post-list">{items}</ul></div>'''
    out += foot(); write('/guides/', out)
    for g in GUIDES:
        crumbs = [('Home', '/'), ('Guides', '/guides/'), (g['short'], g['path'])]
        art = {'@context': 'https://schema.org', '@type': 'Article', 'headline': g['title'], 'description': g['description'],
               'datePublished': g['published'], 'dateModified': g['checked'], 'inLanguage': 'en-GB', 'author': person_ld(),
               'publisher': {'@type': 'Organization', 'name': NAME, 'url': BASE + '/'},
               'mainEntityOfPage': {'@type': 'WebPage', '@id': BASE + g['path']}, 'url': BASE + g['path']}
        ld = [art, crumb_ld(crumbs)] + ([faq_ld(g['qas'])] if g['qas'] else [])
        raw_title = g.get('meta_title') or g['short']
        unmtd = re.sub(r'\bMTD\b', 'Making Tax Digital', raw_title)
        out = head(choose_title([
            raw_title,
            unmtd,
            f"{unmtd} | {NAME}",
            f"{raw_title} | {NAME}",
        ]), g.get('meta_description') or g['description'], g['path'], ld, og_type='article')
        faqs = ('<h2>Quick answers</h2>' + faq_html(g['qas'])) if g['qas'] else ''
        out += f'''<article class="wrap" style="max-width:980px"><p class="breadcrumb"><a href="/">Home</a> › <a href="/guides/">Guides</a> › {E(g["short"])}</p>
<h1>{E(g["title"])}</h1>
<p class="byline">By <a href="/about/">{E(OPERATOR)}</a> · Facts checked {E(nice_date(g["checked"]))}</p>
{g["html"]}
{faqs}
<p class="note-footer">This page gives general information about the options available. It is not tax, legal or financial advice, and we don't tell you which option to choose. Prices and plans change, so check the provider's own website. See our <a href="/affiliate-disclosure/">affiliate disclosure</a> and <a href="/methodology/">how we check</a>.</p>
</article>'''
        if 'unverified-dialog' in g['html']:
            out += '<script src="/assets/unverified.js" defer></script>'
        out += foot(); write(g['path'], out)


# ---------- Founders Blog (data/blog/*.md) ----------
def md_inline(text):
    pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)|\*\*(.+?)\*\*|\*(.+?)\*')
    parts, pos = [], 0
    for m in pattern.finditer(text):
        parts.append(E(text[pos:m.start()]))
        if m.group(1) is not None:
            href = m.group(2)
            rel = ' rel="noopener"' if href.startswith(('http://', 'https://')) else ''
            parts.append(f'<a href="{E(href)}"{rel}>{E(m.group(1))}</a>')
        elif m.group(3) is not None:
            parts.append(f'<strong>{E(m.group(3))}</strong>')
        else:
            parts.append(f'<em>{E(m.group(4))}</em>')
        pos = m.end()
    parts.append(E(text[pos:]))
    return ''.join(parts)

def md_to_html(text):
    blocks, buf, mode = [], [], None
    def flush():
        nonlocal buf, mode
        if not buf:
            return
        if mode == 'ul':
            blocks.append('<ul>' + ''.join(f'<li>{md_inline(x)}</li>' for x in buf) + '</ul>')
        elif mode == 'ol':
            blocks.append('<ol>' + ''.join(f'<li>{md_inline(x)}</li>' for x in buf) + '</ol>')
        else:
            blocks.append('<p>' + md_inline(' '.join(buf)) + '</p>')
        buf, mode = [], None
    for line in text.splitlines():
        if not line.strip():
            flush(); continue
        hm = re.match(r'^(#{1,3}) (.+)$', line)
        if hm:
            flush(); n = len(hm.group(1)); blocks.append(f'<h{n}>{md_inline(hm.group(2))}</h{n}>'); continue
        um = re.match(r'^[-*] (.+)$', line)
        if um:
            if mode != 'ul':
                flush(); mode = 'ul'
            buf.append(um.group(1)); continue
        om = re.match(r'^\d+\. (.+)$', line)
        if om:
            if mode != 'ol':
                flush(); mode = 'ol'
            buf.append(om.group(1)); continue
        if mode not in (None, 'p'):
            flush()
        mode = 'p'
        buf.append(line)
    flush()
    return '\n'.join(blocks)

def load_posts():
    folder = os.path.join(ROOT, 'data', 'blog')
    posts = []
    if not os.path.isdir(folder):
        return posts
    for fn in sorted(os.listdir(folder)):
        if not fn.endswith('.md'):
            continue
        raw = open(os.path.join(folder, fn), encoding='utf-8').read()
        if not raw.startswith('---'):
            raise SystemExit(f'Blog post {fn} needs front matter between --- lines')
        parts = raw.split('---', 2)
        if len(parts) < 3:
            raise SystemExit(f'Blog post {fn} front matter is not closed')
        meta = {}
        for line in parts[1].strip().splitlines():
            if not line.strip() or line.strip().startswith('#'):
                continue
            k, _, v = line.partition(':')
            meta[k.strip()] = v.strip().strip('"').strip("'")
        for req in ('title', 'date'):
            if not meta.get(req):
                raise SystemExit(f'Blog post {fn} is missing {req}')
        posts.append({
            'slug': fn[:-3], 'title': meta['title'], 'date': meta['date'],
            'author': meta.get('author') or OPERATOR, 'description': meta.get('description') or '',
            'html': md_to_html(parts[2].strip()), 'path': f'/founders-blog/{fn[:-3]}/',
        })
    posts.sort(key=lambda p: p['date'], reverse=True)
    return posts

POSTS = load_posts()

def blog_pages():
    il = {'@context': 'https://schema.org', '@type': 'Blog', 'name': f'Founders Blog · {NAME}',
          'url': BASE + '/founders-blog/', 'inLanguage': 'en-GB', 'author': person_ld(),
          'blogPost': [{'@type': 'BlogPosting', 'headline': p['title'], 'url': BASE + p['path'],
                        'datePublished': p['date'], 'author': person_ld()} for p in POSTS]}
    items = ''.join(
        f'''<li><p class="byline">{E(nice_date(p["date"]))} · {E(p["author"])}</p>
<h2><a href="{p["path"]}">{E(p["title"])}</a></h2>
<p>{E(p["description"])}</p>
<p><a href="{p["path"]}">Read the post →</a></p></li>''' for p in POSTS) or '<li><p>No posts yet.</p></li>'
    out = head(choose_title([
        f'Founders Blog from the site operator | {NAME}',
        f'Founders Blog | {NAME}',
    ]),
               f'Notes from {OPERATOR} on building {NAME}, a plain-English comparison of Making Tax Digital software.',
               '/founders-blog/', [il, crumb_ld([('Home', '/'), ('Founders Blog', '/founders-blog/')])])
    out += f'''<div class="wrap prose">
<p class="breadcrumb"><a href="/">Home</a> › Founders Blog</p>
<h1>Founders Blog</h1>
<p class="lead">Notes from {E(OPERATOR)} on why this site exists and how we compare Making Tax Digital software in plain English.</p>
<ul class="post-list">{items}</ul>
<p class="note-footer">Written by {E(OPERATOR)}, UK. Questions or corrections: {contact_html() if CONTACT_EMAIL else 'contact email coming soon'}. <a href="/about/">About {E(OPERATOR)}</a>.</p>
</div>'''
    out += foot(); write('/founders-blog/', out)
    for p in POSTS:
        post_ld = {
            '@context': 'https://schema.org', '@type': 'BlogPosting',
            'headline': p['title'], 'description': p['description'] or p['title'],
            'datePublished': p['date'], 'dateModified': p['date'], 'inLanguage': 'en-GB',
            'author': person_ld(),
            'publisher': {'@type': 'Organization', 'name': NAME, 'url': BASE + '/'},
            'mainEntityOfPage': {'@type': 'WebPage', '@id': BASE + p['path']},
            'url': BASE + p['path'],
        }
        crumbs = [('Home', '/'), ('Founders Blog', '/founders-blog/'), (p['title'], p['path'])]
        out = head(choose_title([
            f"{p['title']} | Founders Blog | {NAME}",
            f"{p['title']} | Founders Blog",
            p['title'],
        ]), p['description'] or p['title'], p['path'],
                   [post_ld, crumb_ld(crumbs)], og_type='article')
        out += f'''<article class="wrap prose">
<p class="breadcrumb"><a href="/">Home</a> › <a href="/founders-blog/">Founders Blog</a> › {E(p["title"])}</p>
<h1>{E(p["title"])}</h1>
<p class="byline">{E(nice_date(p["date"]))} · {E(p["author"])}</p>
<div class="post-body">{p["html"]}</div>
<p class="note-footer">This site gives general information, not personal tax advice. <a href="/about/">About {E(OPERATOR)}</a>.</p>
</article>'''
        out += foot(); write(p['path'], out)

def other_pages():
    simple('/methodology/', 'How we check our prices and sources', 'Where our MTD software data comes from, how we check prices, and what "unknown" means.', f'''
<p class="lead">Our rule is simple: we only show a fact if we can point to where it came from. If we can't confirm something, we say "Unknown" rather than guess.</p>
<h2>Where the data comes from</h2>
<ul><li><strong>Which products are listed, and their features:</strong> <a href="{FINDER}">HMRC's software finder for Making Tax Digital for Income Tax</a>, using the full list for sole traders and landlords. Last read on {nice_date(HMRC_DATE)}: {len(products)} products. This gives us whether there's a free version, whether it creates records or bridges to spreadsheets, which income sources it supports, what it can submit, MTD for VAT, HMRC Assist, accessibility features and the status of each tax-return item.</li>
<li><strong>Prices:</strong> read by us on each provider's own pricing page. Each product page shows the date checked and links to the page. We note introductory offers separately from the regular price. So far we've checked {len(CHECKEDP)} products, starting with the best-known names and those people ask about most on forums.</li>
<li><strong>Joint property support:</strong> shown as "Yes" only when the provider's own site says it splits income and expenses between joint owners. HMRC's finder doesn't record this. See <a href="/guides/jointly-owned-property-mtd/">our jointly owned property guide</a>.</li>
<li><strong>CIS:</strong> "CIS on tax return" is HMRC's status for reporting Construction Industry Scheme deductions on your tax return. It doesn't mean the software files contractor CIS returns.</li>
<li><strong>Thresholds and dates:</strong> taken directly from GOV.UK and linked wherever they appear.</li></ul>
<h2>Order and independence</h2>
<p>The directory shows our <strong>featured</strong> products first. These are products whose providers run an affiliate programme we can join, so featuring them is a commercial decision, not a purely editorial ranking. Every other HMRC-recognised product follows under <strong>Best of the rest</strong>. Within each group, the default order is price-checked products first, then paid plans before their free variants (for example Clear Books before Clear Books Free), then A to Z. Free variants stay in the list, and if you filter to free versions only you still see them. You can also re-sort the table yourself. Right now no affiliate links are live, so a commission does not change this order. A commission never decides whether a product is listed or what facts we show: every product's details come from HMRC and the provider's own website, checked the same way.</p>
<h2>Which pages search engines see</h2>
<p>Every HMRC-recognised product has a page, and every page stays linked from the directory. We release product pages to search engines gradually: until a page has information we've checked on the provider's own website, it's kept out of search results, so we don't publish thin pages.</p>
<h2>Who checks</h2>
<p>This site is run by {E(OPERATOR)} in the UK, for UK landlords and sole traders. AI helps gather and organise the details, and {E(OPERATOR)} checks the results before anything is published. <a href="/about/">About {E(OPERATOR)}</a>.</p>
<h2>Keeping it up to date</h2>
<p>We re-read HMRC's list and re-check prices regularly. If you spot something out of date, {('email ' + contact_html() + ' and we will correct it.') if CONTACT_EMAIL else 'a corrections email is coming soon.'}</p>''',
           [('Home', '/'), ('How we check', '/methodology/')])
    about_person = person_ld()
    about_person['description'] = (
        "I've spent 20 years working in finance in London, in debt purchasing, complaints handling "
        "and credit control for a consumer loan company, and I've also trained and managed teams of new starters."
    )
    about_person['mainEntityOfPage'] = BASE + '/about/'
    about_crumbs = [('Home', '/'), ('About Daniel Wyatt', '/about/')]
    about_body = f'''
<p class="lead">I've spent 20 years working in finance in London, in debt purchasing, complaints handling and credit control for a consumer loan company, and I've also trained and managed teams of new starters. That means I've seen money matters from both sides: how businesses and regulators talk, and how hard that language can be for the people on the receiving end.</p>
<p>I built this site to close that gap. Making Tax Digital is a big change for landlords and sole traders, and most of what's written about it is either jargon or a sales pitch. Here you'll get plain English, the facts checked against GOV.UK and the software providers' own websites, and a clear way to compare your options.</p>
<p>I use AI to gather and organise the details quickly, but a person always checks the results before anything goes on this site. Where I earn a commission, or could, I'll always tell you. Those products are shown in a labelled Featured section, and the facts about every product are checked the same way.</p>
<p class="note-footer">This site gives general information, not personal tax advice.</p>
<h2>What this site is</h2>
<p>A plain-English, independent comparison of software HMRC recognises for Making Tax Digital for Income Tax, built from HMRC's own list and the providers' own websites. It's run by me, {E(OPERATOR)}, founder of {operator_org_link()}, in the UK, and written for UK landlords and sole traders.</p>
<h2>What this site isn't</h2>
<p>It isn't HMRC, it isn't connected with any government body, and it doesn't give tax advice.</p>
<h2>Contact</h2>
<p>{contact_html()}.</p>'''
    out = head(choose_title([
        f'About Daniel Wyatt, who runs the site | {NAME}',
        f'About Daniel Wyatt | {NAME}',
    ]), f'Who runs {NAME} and why. {OPERATOR} on 20 years in London finance and a plain-English comparison of Making Tax Digital software.', '/about/', [about_person, crumb_ld(about_crumbs)])
    out += f'<div class="wrap prose"><p class="breadcrumb"><a href="/">Home</a> › About Daniel Wyatt</p><h1>About Daniel Wyatt</h1>{about_body}</div>'
    out += foot(); write('/about/', out)
    live = [p for p in products if p['affiliate_url']]
    if EMAIL_ON:
        aff_emails = "If you get our Free MTD Ready Kit, our emails may sometimes mention software we earn a commission from. When they do, we say so in the email, and the same rules apply: a commission never changes what we recommend."
    else:
        aff_emails = "We do not send a kit mailing list at the moment. The kit is a free download, and you do not need to give us an email address. If we later offer optional reminder emails, and those emails mention software we earn a commission from, we will say so in the email, and the same rules will apply: a commission never changes what we recommend."
    simple('/affiliate-disclosure/', 'Affiliate disclosure: how this comparison may be funded', 'How this site makes money and how affiliate links are marked.', f'''
<p class="lead">This site is free to use. To pay for it, we may earn a commission when you sign up for some software through links on this site.</p>
<h2>Right now</h2>
<p>{f"Affiliate links are live for: {', '.join(E(p['name']) for p in live)}." if live else "No affiliate links are live yet. Every link goes to the provider's official website, as listed by HMRC."}</p>
<h2>How affiliate links are marked</h2>
<ul><li>Next to every affiliate button we say it's an affiliate link.</li><li>Affiliate links carry <code>rel="sponsored nofollow"</code>, so search engines know they're paid links.</li><li>Featured products are the ones we may earn a commission from, and they're shown first on the homepage and in "alternatives" lists. That placement is commercial. Within each group, the default order lists paid plans before their free variants, then A to Z; that is not a commission ranking, and right now no affiliate links are live. A commission never decides whether a product is listed or what facts we show about it: every product's facts are checked the same way, and every HMRC-recognised product stays in the full list.</li></ul>
<h2>Our emails</h2>
<p>{aff_emails}</p>
<h2>Other ways we may earn in future</h2>
<p>If we ever show sponsored placements or refer you to an accountant for a fee, we'll label it clearly on the page where it appears.</p>''', [('Home', '/'), ('Affiliate disclosure', '/affiliate-disclosure/')])
    simple('/privacy/', 'Privacy information for this site', 'Privacy information for this site.', '''
''' + privacy_body(), [('Home', '/'), ('Privacy', '/privacy/')])
    out = head(f'Page not found | {NAME}', 'Page not found.', '/404.html', noindex=True)
    out += '<div class="wrap"><h1>Page not found</h1><p><a href="/">Go to the MTD software comparison</a></p></div>' + foot()
    write('/404.html', out)

def email_privacy():
    if not EMAIL_ON:
        return ('<h2 id="email">Email sign-up</h2><p>The Free MTD Ready Kit is available to download from this site. You do not need to give us your name or email address to get it, and we do not run a mailing list at the moment.</p>'
                '<p>If you email us with a question, we use your email address and anything you write only to reply to you. We don\'t add you to a list.</p>'
                '<p>If we later offer optional email reminders, this section will explain exactly what we collect and why, before any sign-up form goes live.</p>')
    prov = {'brevo': ('Brevo (Sendinblue SAS, France)', 'https://www.brevo.com/legal/privacypolicy/', 'Brevo stores the list on servers in the European Union.'),
            'mailerlite': ('MailerLite', 'https://www.mailerlite.com/legal/privacy-policy', ''),
            'kit': ('Kit (ConvertKit LLC, USA)', 'https://kit.com/privacy', '')}.get(EMAIL['provider'], (EMAIL['provider'], '', ''))
    pl = f'<a href="{prov[1]}" rel="noopener">{E(prov[0])}</a>' if prov[1] else E(prov[0])
    track = (' Our emails contain standard measurement that tells us whether an email was opened and which links were clicked. We use this only to see which emails are useful and to stop emailing addresses that never open anything.'
             if EMAIL.get('emails_track_opens_and_clicks', True) else '')
    return f"""<h2 id="email">Email sign-up (Free MTD Ready Kit)</h2>
<p>If you sign up for our Free MTD Ready Kit we collect your <strong>first name</strong>, <strong>email address</strong> and, only if you choose to tell us, whether you're a landlord, sole trader, both, or an accountant. We also keep a record of when you signed up and confirmed, so we can show you agreed.</p>
<p><strong>What we use it for:</strong> to send you the kit, a reminder before each Making Tax Digital deadline, and occasional plain-English MTD tips. Some tips may mention software we earn a commission from, and we always say so. We use the "I am a…" answer only to send you reminders that fit your situation.{track}</p>
<p><strong>Lawful basis:</strong> your consent, which you give by submitting the form and then clicking the confirmation link we email you (double opt-in). You can withdraw it at any time with the unsubscribe link in every email, or by contacting us.</p>
<p><strong>Who handles it:</strong> {pl} sends our emails and stores the list on our behalf, under a data processing agreement. {prov[2]} We never sell your details or share them with software providers, accountants or advertisers.</p>
<p><strong>How long we keep it:</strong> until you unsubscribe. After that we keep only your email address on a suppression list, so we don't email you again by mistake. If you never confirm your sign-up, you're not added to the list.</p>"""

def privacy_body():
    op = (f'<p>This site is operated by {E(OPERATOR)}.</p>'
          + (f'<p>Email: {contact_html()}.</p>' if CONTACT_EMAIL else '<p>Contact email coming soon.</p>')
          + (f'<p>Please contact us by email. We reply to all privacy requests by email.</p>' if not SITE.get('postal_address') else f'<p>Post: {E(SITE["postal_address"])}</p>'))
    if not ANALYTICS_ON:
        return ("<h2>Cookies and visitor statistics</h2><p>This site doesn't use cookies, analytics or tracking at the moment. "
                "If that changes, we'll update this page first.</p>" + email_privacy() + "<h2>Other websites</h2><p>When you click through to a software provider, their own privacy policy applies.</p>"
                "<h2>Your rights and contact</h2><p>You can ask us for a copy of your data, or to correct or delete it, and you can complain to the <a href=\"https://ico.org.uk/make-a-complaint/\" rel=\"noopener\">Information Commissioner's Office</a>.</p>" + op)
    prov = {'goatcounter': ('GoatCounter', 'https://www.goatcounter.com/help/privacy')}.get(ANALYTICS['provider'], (ANALYTICS['provider'], ''))
    pl = f'<a href="{prov[1]}" rel="noopener">{prov[0]}</a>' if prov[1] else E(prov[0])
    ev = []
    if ANALYTICS.get('track_outbound_clicks', True): ev.append('when you click a link to another website, such as a software provider\'s "Visit" button: which product or website, and which of our pages you clicked from')
    if ANALYTICS.get('track_start_here', True): ev.append('which "Start here" button you press (for example "I\'m a landlord")')
    if ANALYTICS.get('track_filters', True): ev.append('which comparison filters you switch on. If you type in the search box we only record <em>that</em> a search was used, never what you typed')
    if ANALYTICS.get('track_time_on_page', True): ev.append('roughly how long a page was open and in use (in seconds)')
    if EMAIL_ON and ANALYTICS.get('track_signups', True): ev.append('that the email sign-up form was sent, which page it was on and which "I am a…" option was picked. Never your name or email address')
    return f"""<h2>Cookies</h2>
<p>This site doesn't set cookies and doesn't store anything on your device to measure visits. The only exception is if you use the button below to turn analytics off: your browser then remembers that choice.</p>
<h2>Visitor statistics</h2>
<p>We use {pl}, a privacy-friendly analytics service, to count visits so we can see which pages help people and improve the site. It doesn't use cookies and doesn't build a profile of you. For each page view it records:</p>
<ul><li>the page address and title, and the website that sent you here (for example a search engine)</li>
<li>your browser and operating system type, screen size, and country or region (worked out from your IP address)</li>
<li>a random visit ID so a reload isn't counted twice. Your IP address and full browser details are only held in the service's memory, for up to 8 hours, to create this ID. They are never saved</li></ul>
<p>We also count a few actions on our pages:</p><ul>{''.join(f'<li>{x}</li>' for x in ev)}</ul>
<p>Visitor statistics never include your name, email or anything you type. We only look at the results as totals, such as "120 visits to this page", and we don't use them for advertising or to identify anyone. {E(prov[0])} processes the data on our behalf.</p>
<p>Our lawful basis is legitimate interests: understanding how the site is used so we can improve it. You can object at any time:</p>
<p><button type="button" class="btn ghost" id="mtd-optout">Turn off analytics for this browser</button> <span id="mtd-optout-status" class="disclose"></span></p>
<p class="disclose">We also don't count visits if your browser sends a "Do Not Track" or "Global Privacy Control" signal.</p>
""" + email_privacy() + f"""<h2>Other websites</h2><p>When you click through to a software provider, their own privacy policy applies. If a link is an affiliate link, the provider may use its own cookies to record that you came from us. See our <a href="/affiliate-disclosure/">affiliate disclosure</a>.</p>
<h2>Your rights and contact</h2><p>You can ask us for a copy of your data, or to correct or delete it, and you can complain to the <a href="https://ico.org.uk/make-a-complaint/" rel="noopener">Information Commissioner's Office</a>.</p>""" + op

# Named crawlers get their own group (robots.txt uses the most specific matching
# User-agent and ignores * in that case), so Allow/Disallow are repeated. /kit/
# stays disallowed for everyone, including AI crawlers.
AI_CRAWLERS = [
    'OAI-SearchBot', 'ChatGPT-User', 'GPTBot',
    'ClaudeBot', 'Claude-SearchBot', 'Claude-User',
    'PerplexityBot', 'Perplexity-User',
]
SEARCH_CRAWLERS = ['Googlebot', 'Bingbot']

def robots_txt():
    rules = 'Allow: /\nDisallow: /kit/\n'
    named = '\n'.join(f'User-agent: {ua}' for ua in AI_CRAWLERS + SEARCH_CRAWLERS)
    return (
        '# AI search and assistant crawlers, plus Googlebot and Bingbot, are welcome.\n'
        '# The same rules apply to everyone: the site is open, except the kit files under /kit/.\n\n'
        f'{named}\n{rules}\n'
        f'User-agent: *\n{rules}\n'
        f'Sitemap: {BASE}/sitemap.xml\n'
    )

def llms_submits_phrase(submits):
    parts = [x.strip() for x in (submits or '').split(',') if x.strip() and x.strip().lower() != 'unknown']
    if not parts:
        return None
    mapped = []
    for x in parts:
        xl = x.lower()
        mapped.append('the tax return' if xl == 'tax return' else xl)
    if len(mapped) == 1:
        return f'Submits {mapped[0]}.'
    return 'Submits ' + ', '.join(mapped[:-1]) + ' and ' + mapped[-1] + '.'

def llms_product_note(p):
    inc = incomes(p)
    lead = 'HMRC-recognised Making Tax Digital for Income Tax software'
    if inc:
        joined = inc[0] if len(inc) == 1 else ', '.join(inc[:-1]) + ' and ' + inc[-1]
        lead += ' for ' + joined
    bits = [lead + '.']
    if p.get('price_text') and p['price_text'] != 'unknown':
        bits.append(p['price_text'] + '.')
    typ = []
    if p['creates_records'] == 'yes':
        typ.append('creates digital records')
    if p['bridging'] == 'yes':
        typ.append('can be used as bridging software')
    if typ:
        bits.append(typ[0].capitalize() + (' and ' + typ[1] if len(typ) > 1 else '') + '.')
    sub = llms_submits_phrase(p.get('submits'))
    if sub:
        bits.append(sub)
    return ' '.join(bits)

def llms_txt():
    """Curated /llms.txt (llmstxt.org): key pages plus featured, indexable product pages."""
    def item(title, path, note):
        return f'- [{title}]({BASE}{path}): {note}'
    lines = [
        f'# {NAME}',
        '',
        f'> {SITE["tagline"]} for UK landlords and sole traders.',
        '',
        f'The site is run by {OPERATOR} in London. It is written for UK landlords and sole traders facing Making Tax Digital for Income Tax from 6 April 2026 (qualifying income over £50,000 in the 2024 to 2025 tax year), 6 April 2027 (over £30,000 in 2025 to 2026), or 6 April 2028 (over £20,000 in 2026 to 2027).',
        '',
        "It is a plain-English, independent comparison of software HMRC recognises for Making Tax Digital for Income Tax, built from HMRC's own list and the providers' own websites. Prices are checked on each provider's own pricing page. Some links may earn a commission. Featured products are ones whose providers run an affiliate programme, and they are shown first: that placement is commercial, not a purely editorial ranking. Within each group, paid plans are listed before free variants, then A to Z. Right now no affiliate links are live, so a commission does not change this order. A commission never decides whether a product is listed or what facts are shown.",
        '',
        'This site gives general information only. It is not tax, legal or financial advice.',
        '',
        f'Contact: {CONTACT_EMAIL}' if CONTACT_EMAIL else 'Contact: see the About page.',
        '',
        '## Key pages',
        '',
        item('Home', '/', f'Compare all {len(products)} HMRC-recognised Making Tax Digital for Income Tax products. Pick who you are and what you need to see matching software. Prices checked at source.'),
        item('Do I need Making Tax Digital, and when?', '/do-i-need-mtd/', 'Who needs MTD for Income Tax, the thresholds, quarterly deadlines and exemptions, all sourced from GOV.UK.'),
        item('Making Tax Digital guides', '/guides/', "Plain-English guides to Making Tax Digital for Income Tax for landlords and sole traders, checked against GOV.UK and providers' own websites."),
    ]
    for g in GUIDES:
        lines.append(item(g['title'], g['path'], g['description']))
    lines += [
        item('Free MTD Ready Kit', '/free-mtd-kit/', ('Free Making Tax Digital for Income Tax kit: every deadline for 2026 to 2028, a getting-ready checklist, a calendar file and email reminders 7 days before each HMRC deadline. Sourced from GOV.UK.' if EMAIL_ON else 'Free Making Tax Digital for Income Tax kit: every deadline for 2026 to 2028, a getting-ready checklist, and a calendar file with an alert 7 days before each HMRC deadline. Download from the page; no email address needed. Sourced from GOV.UK.')),
        item('How we check', '/methodology/', 'Where the software data comes from, how prices are checked, what "unknown" means, and how the directory is ordered.'),
        item('About Daniel Wyatt', '/about/', f'Who runs {NAME} and why. {OPERATOR} on 20 years in London finance and a plain-English comparison of Making Tax Digital software.'),
        item('Affiliate disclosure', '/affiliate-disclosure/', 'How this site makes money and how affiliate links are marked.'),
        item('Privacy', '/privacy/', 'Privacy information for this site.'),
        '',
        '## Featured MTD software',
        '',
        f'These {len(FEATURED)} products are shown first on the homepage because their providers run an affiliate programme. Facts below are from HMRC and each provider\'s own website, checked the same way as every other product. Only indexable product pages are listed here.',
        '',
    ]
    featured_listed = [p for p in FEATURED if p['slug'] in INDEXABLE]
    for p in featured_listed:
        lines.append(item(p['name'], f"/software/{p['slug']}/", llms_product_note(p)))
    if not featured_listed:
        lines.append('No featured product pages are currently released for indexing.')
    lines.append('')
    return '\n'.join(lines) + '\n'

def seo_files():
    build_date = datetime.date.today().isoformat()
    urls = [('/', CHECKED), ('/do-i-need-mtd/', CHECKED), ('/free-mtd-kit/', CHECKED), ('/methodology/', CHECKED),
            ('/about/', CHECKED), ('/founders-blog/', CHECKED), ('/affiliate-disclosure/', CHECKED), ('/privacy/', CHECKED)]
    urls += [(p['path'], p['date']) for p in POSTS]
    urls += [('/guides/', max([g['checked'] for g in GUIDES] + [CHECKED]))] + [(g['path'], g['checked']) for g in GUIDES]
    urls += [(f"/software/{p['slug']}/", p['price_checked'] or CHECKED) for p in products if p['slug'] in INDEXABLE]
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(f'<url><loc>{BASE}{u}</loc><lastmod>{build_date}</lastmod></url>\n' for u, lm in urls) + '</urlset>\n'
    write('/sitemap.xml', sm)
    write('/robots.txt', robots_txt())
    write('/llms.txt', llms_txt())
    write('/CNAME', 'mtdsoftwarecompare.co.uk\n')

if __name__ == '__main__':
    if os.path.exists(DIST): shutil.rmtree(DIST)
    os.makedirs(f'{DIST}/assets')
    shutil.copy(f'{ROOT}/src/favicon.ico', f'{DIST}/favicon.ico')
    shutil.copy(f'{ROOT}/src/favicon.svg', f'{DIST}/assets/favicon.svg')
    shutil.copy(f'{ROOT}/src/favicon-32.png', f'{DIST}/assets/favicon-32.png')
    shutil.copy(f'{ROOT}/src/apple-touch-icon.png', f'{DIST}/assets/apple-touch-icon.png')
    shutil.copy(f'{ROOT}/src/og-image.png', f'{DIST}/assets/og-image.png')
    shutil.copy(f'{ROOT}/src/style.css', f'{DIST}/assets/style.css')
    shutil.copy(f'{ROOT}/src/directory.js', f'{DIST}/assets/directory.js')
    shutil.copy(f'{ROOT}/src/funnel.js', f'{DIST}/assets/funnel.js')
    shutil.copy(f'{ROOT}/src/unverified.js', f'{DIST}/assets/unverified.js')
    if ANALYTICS_ON: shutil.copy(f'{ROOT}/src/analytics.js', f'{DIST}/assets/analytics.js')
    if EMAIL_ON: shutil.copy(f'{ROOT}/src/signup.js', f'{DIST}/assets/signup.js')
    for i in (1, 2): shutil.copy(f'{ROOT}/src/kit-preview-{i}.png', f'{DIST}/assets/kit-preview-{i}.png')
    os.makedirs(f'{DIST}/kit')
    for f in (KIT_PDF, KIT_ICS): shutil.copy(ROOT + f, DIST + f)
    json.dump({'source': HM['source'], 'hmrc_retrieved': HMRC_DATE, 'vendor_checked': CHECKED, 'count': len(products), 'products': products},
              open(f'{ROOT}/data/products.json', 'w'), indent=1, ensure_ascii=False)
    os.makedirs(f'{DIST}/data'); shutil.copy(f'{ROOT}/data/products.json', f'{DIST}/data/products.json')
    home(); guide(); other_pages(); blog_pages(); guide_pages(); kit_pages(); seo_files()
    for p in products: product_page(p)
    missing = [k for k in VV['products'] if k not in {p['name'] for p in products}]
    print('Email sign-up:', f"{EMAIL['provider']} ({EMAIL['form_action']})" if EMAIL_ON else 'OFF: kit is a direct download (config/email.json has no provider/form_action)')
    print('Analytics:', f"{ANALYTICS['provider']} ({ANALYTICS['site_id']})" if ANALYTICS_ON else 'OFF (config/analytics.json has no provider/site_id)')
    print(f'Built {len(products)} product pages ({len(CHECKEDP)} vendor-checked; {len(INDEXABLE)} indexable, {len(products) - len(INDEXABLE)} noindex per config/indexing.json). Unmatched vendor keys: {missing}')
