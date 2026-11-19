#!/usr/bin/env python3
"""Build the Free MTD Ready Kit lead magnet from data/deadlines.json:
   kit/mtd-ready-kit-2026-28.pdf      (A4 PDF, rendered with Playwright/Chromium)
   kit/mtd-deadlines-2026-28.ics      (calendar file, each event with a 7-day alarm)
   kit/kit.html                       (the PDF's source, for review)
   src/kit-preview-1.png, -2.png      (page previews used on /free-mtd-kit/)
Re-run after changing the site name or the deadlines:  python3 scripts/make_kit.py"""
import json, os, datetime as dt, html, hashlib
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = json.load(open(f'{ROOT}/config/site.json'))
D = json.load(open(f'{ROOT}/data/deadlines.json'))
NAME = SITE['name']; OPERATOR = (SITE.get('operator_name') or '').strip() or 'Daniel Wyatt'; E = html.escape

def logo_html():
    if ' ' in NAME:
        lead, _, accent = NAME.rpartition(' ')
        return f'{E(lead)} <span>{E(accent)}</span>'
    return f'<span>{E(NAME)}</span>'

SRC = D['sources']
def d(iso): return dt.date.fromisoformat(iso)
def nice(x, wd=True): return (x.strftime('%a ') if wd else '') + f'{x.day} {x.strftime("%B %Y")}'
CHECKED = nice(d(D['checked']), False)
WEEKEND = lambda x: x.weekday() >= 5

# ---- quarterly table for two full tax years (2026-27 Q1/Q2 already passed but shown for completeness)
Q = [('2026 to 2027', [('6 April to 5 July 2026', '1 April to 30 June 2026', '2026-08-07'), ('6 April to 5 October 2026', '1 April to 30 September 2026', '2026-11-07'),
                      ('6 April 2026 to 5 January 2027', '1 April to 31 December 2026', '2027-02-07'), ('6 April 2026 to 5 April 2027', '1 April 2026 to 31 March 2027', '2027-05-07')]),
     ('2027 to 2028', [('6 April to 5 July 2027', '1 April to 30 June 2027', '2027-08-07'), ('6 April to 5 October 2027', '1 April to 30 September 2027', '2027-11-07'),
                      ('6 April 2027 to 5 January 2028', '1 April to 31 December 2027', '2028-02-07'), ('6 April 2027 to 5 April 2028', '1 April 2027 to 31 March 2028', '2028-05-07')])]
today = dt.date(2026, 11, 18)
qrows = ''
for ty, rows in Q:
    qrows += f'<tr class="ty"><td colspan="4">Tax year {ty}</td></tr>'
    for i, (std, cal, due) in enumerate(rows, 1):
        x = d(due); past = x < today
        qrows += (f'<tr class="{"past" if past else ""}"><td>Update {i}</td><td>{std}<br><small>Calendar: {cal}</small></td>'
                  f'<td><b>{nice(x)}</b>{" <span class=wk>weekend</span>" if WEEKEND(x) else ""}{" <small>(passed)</small>" if past else ""}</td><td class="box"></td></tr>')

KIND = {'update': 'Quarterly update', 'return': 'Tax return', 'payment': 'Payment', 'start': 'MTD start'}
evrows = ''.join(f'<tr><td><b>{nice(d(e["date"]))}</b>{" <span class=wk>weekend</span>" if WEEKEND(d(e["date"])) else ""}</td><td><span class="k {e["kind"]}">{KIND[e["kind"]]}</span></td><td>{E(e["title"])}<br><small>{E(e["who"])}</small></td></tr>' for e in D['events'])

def cl(items): return '<ul class="cl">' + ''.join(f'<li><span class="tick"></span><div>{i}</div></li>' for i in items) + '</ul>'
ready = cl([
 '<b>Work out your qualifying income.</b> Add your self-employment and property income <em>before expenses</em> from your latest tax return. Salary, dividends, pensions and partnership profit don\'t count.',
 '<b>Find your start date</b> using the table on page 1. HMRC writes to people it expects to qualify, but if you don\'t get a letter it is still your responsibility to check.',
 '<b>Check whether you\'re exempt.</b> £20,000 or less is automatically exempt. Some people, for example those who are digitally excluded, can apply for an exemption.',
 '<b>Choose HMRC-recognised software</b> that covers your income types (self-employment, UK or foreign property), and check it can submit your tax return too, or pair it with one that can.',
 '<b>Decide: standard or calendar update periods.</b> Use calendar periods (1 April to 31 March) only if that is your accounting period. Set it in your software <em>before</em> your first update, because you can\'t change it for the rest of the tax year.',
 '<b>Sign up for MTD for Income Tax</b> on GOV.UK with your Self Assessment sign-in details, or ask your agent to. Have your business name, address, trade and any recent start dates ready.',
 '<b>Authorise your software</b> to talk to HMRC and connect your bank feeds or spreadsheet.',
 '<b>Start digital records from your first day</b> in MTD: every income and expense item, by category.',
 '<b>Jointly let property?</b> Decide whether to include expenses in each quarterly update or add them at year end by resending update 4.',
])
quarter = cl([
 'Bring records up to date for the period (all income and expenses, by category).',
 'Check the totals your software works out. Each update covers the tax year <em>so far</em>, so fix earlier mistakes in your records and they flow into the next update.',
 'Send the update for <b>each</b> business (each self-employment and your property business), even if nothing happened in the period.',
 'Check your HMRC online account says "You sent a quarterly update".',
 'Look at the tax estimate in your software and put money aside.',
])
yearend = cl([
 'After update 4 (due 7 May), make any accounting and tax adjustments, and resend update 4 if your records changed.',
 'Add your other income and gains (for example savings interest, dividends, partnership profit). HMRC adds some items, such as PAYE and pensions, but you must check them.',
 'Submit your tax return through your software by <b>31 January</b>.',
 'Pay your tax by 31 January (and 31 July if you make payments on account). MTD does not change payment dates.',
])

CSS = """@page{size:A4;margin:14mm 14mm 16mm}
*{box-sizing:border-box}body{font:10.5pt/1.45 -apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:#14213d;margin:0}
h1{font-size:22pt;line-height:1.15;margin:0 0 4pt}h2{font-size:14pt;margin:14pt 0 6pt;color:#0b6e4f}h3{font-size:11pt;margin:10pt 0 4pt}
.page{page-break-after:always}.page:last-child{page-break-after:auto}
.top{display:flex;justify-content:space-between;align-items:center;border-bottom:3px solid #0b6e4f;padding-bottom:6pt;margin-bottom:10pt}
.logo{font-weight:800;font-size:13pt}.logo span{color:#0b6e4f}.tag{font-size:8.5pt;color:#5b6475}
.lead{font-size:11.5pt;color:#334}.muted,small{color:#5b6475}small{font-size:8.5pt}
table{width:100%;border-collapse:collapse;font-size:9.5pt;margin:4pt 0}th,td{border-bottom:1px solid #dfe3ea;padding:5pt 6pt;text-align:left;vertical-align:top}
th{background:#eef6f2;font-size:8.5pt;text-transform:uppercase;letter-spacing:.03em}
table.tight td{padding:3.5pt 6pt;line-height:1.3}tr.ty td{background:#14213d;color:#fff;font-weight:700}tr.past td{color:#8a93a3}td.box{width:20pt}td.box:after{content:"";display:inline-block;width:11pt;height:11pt;border:1.5px solid #0b6e4f;border-radius:2pt}
.wk{display:inline-block;background:#fff3cd;color:#7a5a00;font-size:7.5pt;padding:0 4pt;border-radius:6pt;margin-left:3pt}
.k{display:inline-block;font-size:7.5pt;font-weight:700;padding:1pt 5pt;border-radius:6pt;white-space:nowrap}.k.update{background:#e3f1ea;color:#08553d}.k.return{background:#e6ecfb;color:#1f3c88}.k.payment{background:#fdeee0;color:#8a4b00}.k.start{background:#f1e6fb;color:#5a1f88}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:8pt;margin:8pt 0}.box3{border:1px solid #dfe3ea;border-left:4px solid #f2b134;border-radius:5pt;padding:7pt 9pt}.box3 b{display:block;font-size:12pt}
.callout{background:#eef6f2;border:1px solid #cfe5da;border-radius:6pt;padding:8pt 10pt;margin:8pt 0}.warn{background:#fff7e0;border-color:#f0dca0}
ul.cl{list-style:none;padding:0;margin:4pt 0}ul.cl li{display:flex;gap:7pt;margin:0 0 4pt;font-size:9.8pt;line-height:1.38}.tick{flex:0 0 12pt;height:12pt;border:1.5px solid #0b6e4f;border-radius:2pt;margin-top:2pt}
a{color:#0b6e4f;word-break:break-all}.foot{font-size:8pt;color:#5b6475;border-top:1px solid #dfe3ea;margin-top:10pt;padding-top:5pt}
ol.src li{margin-bottom:4pt;font-size:9pt}"""
top = f'<div class="top"><div class="logo">{logo_html()}</div><div class="tag">Free MTD Ready Kit · 2026 to 2028 · checked {CHECKED}</div></div>'
foot = f'<div class="foot">Prepared by {E(OPERATOR)}. General information from GOV.UK, not tax advice. HMRC does not endorse this kit or any software. Contains public sector information licensed under the Open Government Licence v3.0.</div>'
H = f'''<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><title>Free MTD Ready Kit 2026 to 2028 | {E(NAME)}</title><style>{CSS}</style></head><body>
<section class="page">{top}
<h1>Your Making Tax Digital Ready Kit</h1>
<p class="lead">Every MTD for Income Tax deadline from now to January 2029, what to do before you start, and a simple routine for each quarter. Every date comes from GOV.UK.</p>
<h2>1. When do you start?</h2>
<p>It depends on your <b>qualifying income</b>: your self-employment plus property income <em>before expenses</em>, from the tax return for the earlier year.</p>
<div class="grid3"><div class="box3"><b>6 April 2026</b>Over £50,000 in 2024 to 2025<br><small>Already live</small></div>
<div class="box3"><b>6 April 2027</b>Over £30,000 in 2025 to 2026<br><small>Based on the return due 31 January 2027</small></div>
<div class="box3"><b>6 April 2028</b>Over £20,000 in 2026 to 2027<br><small>Based on the return due 31 January 2028</small></div></div>
<p class="muted">£20,000 or less: automatically exempt. You still send a Self Assessment return as normal. You also still send a normal Self Assessment return for the tax year <em>before</em> you start MTD.</p>
<h2>2. What MTD means you do</h2>
<table><tr><th>Task</th><th>How often</th><th>Deadline</th></tr>
<tr><td>Keep digital records of income and expenses in compatible software</td><td>Ongoing</td><td>From day one</td></tr>
<tr><td>Send a quarterly update for each business (summaries, not tax returns)</td><td>4 times a year</td><td>7 Aug, 7 Nov, 7 Feb, 7 May</td></tr>
<tr><td>Submit your tax return through the software, adding any other income</td><td>Once a year</td><td>31 January after the tax year</td></tr>
<tr><td>Pay your tax (unchanged by MTD)</td><td>Once or twice a year</td><td>31 January, and 31 July if you make payments on account</td></tr></table>
<div class="callout warn"><b>Penalties.</b> HMRC won't give penalty points for late quarterly updates in the 2026 to 2027 tax year, but you must still send them before you can submit your tax return. From 2027 to 2028, each late update earns a point and <b>4 points means a £200 penalty</b>. Late tax returns get points in every year.</div>
<div class="callout"><b>Get reminders.</b> Import <b>mtd-deadlines-2026-28.ics</b> (sent with this kit) into Google, Apple or Outlook Calendar: every date below with an alert 7 days before. We'll also email you 7 days before each deadline.</div>
{foot}</section>

<section class="page">{top}
<h2>3. Quarterly update calendar</h2>
<p>The deadlines are the same for standard periods (tax year, 6 April to 5 April) and calendar periods (1 April to 31 March). Each update covers the tax year <em>so far</em>. Tick each one off when it's sent.</p>
<table><tr><th>Update</th><th>Period covered (standard)</th><th>Deadline</th><th>Sent</th></tr>{qrows}</table>
<p class="muted">Several deadlines fall on a weekend. HMRC lists the date itself, so plan to send by the Friday before. You can send an update any time after the period ends, or up to 10 days before it ends if you don't expect any more transactions.</p>
{foot}</section>

<section class="page">{top}
<h2>4. Every key date, in order</h2>
<p>From today to the 2027 to 2028 tax return. These are all in the calendar file that comes with this kit.</p>
<table class="tight"><tr><th>Date</th><th>Type</th><th>What and who</th></tr>{evrows}</table>
{foot}</section>

<section class="page">{top}
<h2>5. Getting-ready checklist</h2>
<p>Do these before your first quarterly update. Most people can do them in an afternoon once the software is chosen.</p>{ready}
<h2>6. Every quarter</h2>{quarter}
<h2>7. After the tax year ends</h2>{yearend}
{foot}</section>

<section class="page">{top}
<h2>8. Sources</h2>
<p>We checked every fact in this kit on GOV.UK on {CHECKED}. HMRC sometimes updates its guidance, so follow the links for the latest version.</p>
<ol class="src">
<li>When you need to start, thresholds and exemptions: <a href="{SRC['eligibility']}">{SRC['eligibility']}</a></li>
<li>Quarterly update periods, deadlines, joint property and penalties: <a href="{SRC['quarterly']}">{SRC['quarterly']}</a></li>
<li>Submitting your tax return through MTD software: <a href="{SRC['tax_return']}">{SRC['tax_return']}</a></li>
<li>Payments on account (31 January and 31 July): <a href="{SRC['payments']}">{SRC['payments']}</a></li>
<li>Signing up, and what you'll need: <a href="{SRC['sign_up']}">{SRC['sign_up']}</a></li>
<li>Qualifying income: <a href="https://www.gov.uk/guidance/work-out-your-qualifying-income-for-making-tax-digital-for-income-tax">https://www.gov.uk/guidance/work-out-your-qualifying-income-for-making-tax-digital-for-income-tax</a></li>
<li>Exemptions: <a href="https://www.gov.uk/guidance/find-out-if-you-can-get-an-exemption-from-making-tax-digital-for-income-tax">https://www.gov.uk/guidance/find-out-if-you-can-get-an-exemption-from-making-tax-digital-for-income-tax</a></li>
<li>HMRC's list of recognised software: <a href="https://www.tax.service.gov.uk/find-making-tax-digital-income-tax-software/">https://www.tax.service.gov.uk/find-making-tax-digital-income-tax-software/</a></li>
</ol>
<h2>Choosing software</h2>
<p>Our free directory compares every product on HMRC's list in plain English, with filters for landlords, sole traders, spreadsheet users (bridging software), CIS and free versions. Prices are checked on each provider's own website.</p>
<div class="callout"><b>Not sure you want to do this yourself?</b> An accountant or bookkeeper can sign you up and send your updates as your agent. HMRC's guidance explains how agents work with MTD.</div>
<p class="muted">This kit is general information, not tax, legal or financial advice. Check your own position on GOV.UK or with a qualified adviser. Prepared by {E(OPERATOR)} for {E(NAME)}, which is independent and is not connected with HMRC.</p>
{foot}</section></body></html>'''
os.makedirs(f'{ROOT}/kit', exist_ok=True)
open(f'{ROOT}/kit/kit.html', 'w').write(H)

# ---- .ics (RFC 5545): future events only, all-day, 7-day alarm
def fold(line):
    b = line.encode(); out = []
    while len(b) > 74:
        cut = 74
        while (b[cut] & 0xC0) == 0x80: cut -= 1
        out.append(b[:cut].decode()); b = b[cut:]
    out.append(b.decode()); return '\r\n '.join(out)
def esc(s): return s.replace('\\', '\\\\').replace(';', '\\;').replace(',', '\\,').replace('\n', '\\n')
stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
L = ['BEGIN:VCALENDAR', 'VERSION:2.0', f'PRODID:-//{NAME}//MTD Ready Kit 2026-28//EN', 'CALSCALE:GREGORIAN', 'METHOD:PUBLISH', f'X-WR-CALNAME:MTD deadlines 2026-28 ({NAME})']
for e in D['events']:
    x = d(e['date'])
    if x < today: continue
    uid = hashlib.sha1((e['date'] + e['title']).encode()).hexdigest()[:16]
    summ = {'update': 'MTD quarterly update due', 'return': 'Tax return due', 'payment': 'Self Assessment payment due', 'start': 'MTD for Income Tax starts'}[e['kind']]
    desc = f"{e['title']}. Who: {e['who'].rstrip('.')}. Source: {SRC[e['src']]} (checked {CHECKED}). General information, not tax advice."
    L += ['BEGIN:VEVENT', f'UID:{uid}@mtd-ready-kit', f'DTSTAMP:{stamp}', f'DTSTART;VALUE=DATE:{x:%Y%m%d}', f'DTEND;VALUE=DATE:{x + dt.timedelta(days=1):%Y%m%d}',
          fold('SUMMARY:' + esc(f'MTD: {e["title"]}')), fold('DESCRIPTION:' + esc(desc)), fold('URL:' + SRC[e['src']]), 'TRANSP:TRANSPARENT',
          'BEGIN:VALARM', 'ACTION:DISPLAY', fold('DESCRIPTION:' + esc(f'In 7 days: {summ}')), 'TRIGGER:-P7D', 'END:VALARM', 'END:VEVENT']
L.append('END:VCALENDAR')
open(f'{ROOT}/kit/mtd-deadlines-2026-28.ics', 'w', newline='').write('\r\n'.join(L) + '\r\n')

# ---- PDF + previews
from playwright.sync_api import sync_playwright
import shutil as _shutil
_chrome = _shutil.which('google-chrome') or _shutil.which('chromium') or _shutil.which('chromium-browser')
_launch = {'args': ['--no-sandbox', '--disable-dev-shm-usage']}
if _chrome:
    _launch['executable_path'] = _chrome
with sync_playwright() as p:
    b = p.chromium.launch(**_launch); pg = b.new_page()
    pg.goto('file://' + f'{ROOT}/kit/kit.html'); pg.wait_for_timeout(300)
    pg.pdf(path=f'{ROOT}/kit/mtd-ready-kit-2026-28.pdf', format='A4', print_background=True, margin={'top': '14mm', 'bottom': '16mm', 'left': '14mm', 'right': '14mm'})
    pv = b.new_page(viewport={'width': 794, 'height': 1123}, device_scale_factor=1)
    pv.goto('file://' + f'{ROOT}/kit/kit.html'); pv.emulate_media(media='print'); pv.wait_for_timeout(200)
    secs = pv.query_selector_all('section.page')
    for i in (0, 1):  # page 1 and the quarterly calendar
        pv.evaluate('i=>{document.querySelectorAll("section.page").forEach((s,j)=>s.style.display=j===i?"block":"none");document.body.style.padding="40px 46px";document.body.style.width="794px"}', i)
        pv.screenshot(path=f'{ROOT}/src/kit-preview-{i + 1}.png', clip={'x': 0, 'y': 0, 'width': 794, 'height': 1123})
    b.close()
print('Wrote kit/mtd-ready-kit-2026-28.pdf, kit/mtd-deadlines-2026-28.ics, kit/kit.html, src/kit-preview-1.png, src/kit-preview-2.png')
